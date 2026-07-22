"""Offline functionality tests: registry/MCP/CLI parity, config gates, and mocked API round-trips."""

import asyncio
import json

import httpx
import pytest

from unifi_tools import api, ssh  # noqa: F401 — importing registers the tools
from unifi_tools.cli import _resolve
from unifi_tools.core import DESTRUCTIVE, REGISTRY, mcp


@pytest.fixture
def creds(monkeypatch):
    monkeypatch.setenv("UNIFI_HOST", "https://controller.test")
    monkeypatch.setenv("UNIFI_API_KEY", "test-key")
    monkeypatch.setenv("UNIFI_SITE_ID", "site-1")
    monkeypatch.delenv("UNIFI_READ_ONLY", raising=False)


@pytest.fixture
def capture(monkeypatch):
    """Route httpx through a mock transport and capture every request."""
    seen = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        data = [{"id": "site-auto", "name": "default"}] if request.url.path.endswith("/v1/sites") else []
        return httpx.Response(200, json={"offset": 0, "limit": 25, "count": len(data), "totalCount": len(data), "data": data})

    real = httpx.AsyncClient
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: real(transport=httpx.MockTransport(handler), timeout=kw.get("timeout")))
    return seen


def test_every_mcp_tool_is_in_registry():
    mcp_names = {t.name for t in asyncio.run(mcp.list_tools())}
    assert mcp_names <= set(REGISTRY), "MCP tool not in CLI registry"
    # When SSH is unconfigured only the 4 SSH tools may be CLI-only.
    assert {n for n in REGISTRY if n not in mcp_names} <= {"unifi_ssh_exec", "unifi_mongo_read", "unifi_mongo_write", "unifi_provision"}


def test_every_tool_resolves_as_cli_command():
    for name in REGISTRY:
        tokens = name.removeprefix("unifi_").split("_")
        resolved, rest = _resolve(tokens)
        assert resolved == name and rest == [], f"{name} does not resolve from `unifi {' '.join(tokens)}`"


def test_reads_and_writes_are_prefix_separable():
    read_verbs = {"list", "get"}
    for t in asyncio.run(mcp.list_tools()):
        verb = t.name.removeprefix("unifi_").split("_")[0]
        if t.annotations and t.annotations.readOnlyHint:
            assert verb in read_verbs or t.name == "unifi_mongo_read", f"read-only {t.name} hides behind a write verb"
        else:
            assert verb not in read_verbs, f"write tool {t.name} masquerades as a read"


def test_destructive_tools_are_flagged():
    for must in ("unifi_delete_network", "unifi_remove_device", "unifi_restart_device", "unifi_bulk_delete_vouchers", "unifi_mongo_write"):
        assert must in DESTRUCTIVE


def test_list_tools_send_pagination_params(creds, capture):
    asyncio.run(REGISTRY["unifi_list_devices"](limit=200, offset=50, filter="name.like('AP*')"))
    q = dict(httpx.QueryParams(capture[0].url.query))
    assert q == {"offset": "50", "limit": "200", "filter": "name.like('AP*')"}
    assert capture[0].url.path == "/proxy/network/integration/v1/sites/site-1/devices"
    assert capture[0].headers["X-API-KEY"] == "test-key"


def test_voucher_list_defaults_to_100(creds, capture):
    asyncio.run(REGISTRY["unifi_list_vouchers"]())
    assert dict(httpx.QueryParams(capture[0].url.query))["limit"] == "100"


def test_read_only_mode_blocks_writes_without_http(creds, capture, monkeypatch):
    monkeypatch.setenv("UNIFI_READ_ONLY", "true")
    out = asyncio.run(REGISTRY["unifi_delete_network"]("net-1"))
    assert "error" in out and "UNIFI_READ_ONLY" in out["error"] and capture == []
    assert "data" in asyncio.run(REGISTRY["unifi_list_networks"]())  # reads still pass


def test_missing_credentials_is_actionable(monkeypatch, capture):
    monkeypatch.delenv("UNIFI_HOST", raising=False)
    monkeypatch.delenv("UNIFI_API_KEY", raising=False)
    monkeypatch.setattr("unifi_tools.core.config_path", lambda: __import__("pathlib").Path("missing.json"))
    out = asyncio.run(REGISTRY["unifi_list_sites"]())
    assert "unifi init" in out["error"]


def test_mongo_write_requires_confirm(monkeypatch):
    monkeypatch.setenv("UNIFI_SSH_PASSWORD", "x")
    out = asyncio.run(REGISTRY["unifi_mongo_write"]("db.device.updateOne({},{})"))
    assert "confirm" in out["error"]


def test_mongo_read_rejects_writes(monkeypatch):
    monkeypatch.setenv("UNIFI_SSH_PASSWORD", "x")
    monkeypatch.delenv("UNIFI_HOST", raising=False)
    monkeypatch.delenv("UNIFI_SSH_HOST", raising=False)
    out = asyncio.run(REGISTRY["unifi_mongo_read"]("db.device.updateMany({},{$set:{}})"))
    assert "unifi_mongo_write" in out["error"]
    # field names containing 'update' are not writes (fails later on missing host, not on the guard)
    out2 = asyncio.run(REGISTRY["unifi_mongo_read"]("db.x.find({updatedAt:1})"))
    assert "unifi_mongo_write" not in out2.get("error", "")


def test_site_auto_resolves_and_caches(monkeypatch, capture):
    import unifi_tools.core as core

    monkeypatch.setenv("UNIFI_HOST", "https://controller.test")
    monkeypatch.setenv("UNIFI_API_KEY", "k")
    monkeypatch.delenv("UNIFI_SITE_ID", raising=False)
    monkeypatch.setattr(core, "_site_cache", None)
    asyncio.run(REGISTRY["unifi_list_devices"]())
    assert capture[0].url.path.endswith("/v1/sites")
    assert capture[1].url.path == "/proxy/network/integration/v1/sites/site-auto/devices"
    asyncio.run(REGISTRY["unifi_list_clients"]())
    assert sum(r.url.path.endswith("/v1/sites") for r in capture) == 1  # cached after first resolve


def test_create_network_round_trip(creds, capture):
    cfg = api.NetworkConfig.model_validate({"name": "IoT", "management": "GATEWAY", "vlanId": 40, "zoneId": "z1"})
    asyncio.run(REGISTRY["unifi_create_network"](cfg))
    body = json.loads(capture[0].content)
    assert capture[0].method == "POST" and body["zoneId"] == "z1" and body["vlanId"] == 40
