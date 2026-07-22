"""Shared core: configuration, the FastMCP instance, the tool registry, and the UniFi API client.

Config resolution order: environment variable, then the config file written by `unifi init`
(%APPDATA%/unifi-tools/config.json on Windows, ~/.config/unifi-tools/config.json elsewhere).
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Awaitable, Callable

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("unifi")

# CLI-facing registry: function name -> coroutine function. Superset of MCP tools
# (SSH tools stay listed here when unconfigured so the CLI can explain how to enable them).
REGISTRY: dict[str, Callable[..., Awaitable[Any]]] = {}
DESTRUCTIVE: set[str] = set()  # tools the CLI gates behind --yes


def config_path() -> Path:
    base = Path(os.environ["APPDATA"]) if sys.platform == "win32" else Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return base / "unifi-tools" / "config.json"


def cfg(key: str, default: str = "") -> str:
    if key in os.environ:
        return os.environ[key]
    try:
        return json.loads(config_path().read_text()).get(key, default)
    except (OSError, ValueError):
        return default


def _truthy(key: str) -> bool:
    return cfg(key).lower() in ("1", "true", "yes")


def tool(read_only: bool = False, destructive: bool = False, idempotent: bool = False, expose_mcp: bool = True):
    """Register a coroutine as a CLI command and (optionally) an MCP tool."""
    def deco(fn):
        REGISTRY[fn.__name__] = fn
        if destructive:
            DESTRUCTIVE.add(fn.__name__)
        if expose_mcp:
            ann = {"readOnlyHint": read_only, "destructiveHint": destructive, "idempotentHint": idempotent}
            mcp.tool(annotations=ann)(fn)
        return fn
    return deco


_site_cache: str | None = None


async def _site(site_id: str | None = None) -> str:
    """Explicit site, configured site, or auto-resolve to the controller's first site."""
    global _site_cache
    sid = site_id or cfg("UNIFI_SITE_ID")
    if sid:
        return sid
    if not _site_cache:
        r = await _api("GET", "/v1/sites")
        sites = r.get("data") if isinstance(r, dict) else None
        if not sites:
            raise ValueError(f"Could not auto-resolve site ({r.get('error', 'no sites returned') if isinstance(r, dict) else r}) — pass site_id or run `unifi init`")
        _site_cache = sites[0]["id"]
    return _site_cache


def _page(offset: int, limit: int, filter: str | None) -> dict:
    return {"offset": offset, "limit": limit, **({"filter": filter} if filter else {})}


def _handle_error(e: Exception) -> str:
    if isinstance(e, httpx.HTTPStatusError):
        r = e.response
        try:
            body = r.json()
            detail = body.get("message") or body
            code = body.get("code", "")
        except ValueError:
            detail, code = r.text, ""
        hints = {401: "Unauthorized — check UNIFI_API_KEY", 403: "Forbidden — API key lacks permission", 404: "Not found — check resource ID", 429: "Rate limited — wait and retry"}
        hint = hints.get(r.status_code, f"HTTP {r.status_code}")
        return f"{hint}{f' [{code}]' if code else ''}: {detail}"
    if isinstance(e, (httpx.TimeoutException, httpx.ConnectError)):
        return f"Cannot reach {cfg('UNIFI_HOST')} ({e or 'timeout'}) — check UNIFI_HOST and network reachability"
    return str(e)


async def _api(method: str, path: str, params: dict | None = None, body: Any = None) -> Any:
    host, key = cfg("UNIFI_HOST"), cfg("UNIFI_API_KEY")
    if not host or not key:
        return {"error": "Set UNIFI_HOST and UNIFI_API_KEY (env vars or `unifi init`)"}
    if method != "GET" and _truthy("UNIFI_READ_ONLY"):
        return {"error": "Blocked: UNIFI_READ_ONLY is set — unset it to allow writes"}
    url = f"{host.rstrip('/')}/proxy/network/integration{path}"
    headers = {"X-API-KEY": key, "Content-Type": "application/json"}
    async with httpx.AsyncClient(verify=_truthy("UNIFI_VERIFY_SSL"), timeout=30) as client:
        try:
            r = await client.request(method, url, headers=headers, params=params, json=body)
            r.raise_for_status()
            return r.json() if r.content else {"status": "ok"}
        except Exception as e:
            return {"error": _handle_error(e)}
