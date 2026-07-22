"""Gateway SSH escape hatch — for the settings the official API does not expose.

Three primitives: raw exec, MongoDB read/write (the controller's ace database, port 27117),
and force-provision (mandatory after any DB write). Enabled only when UNIFI_SSH_KEY or
UNIFI_SSH_PASSWORD is set; host defaults to the controller from UNIFI_HOST, user to root.

Rule: never use SSH for anything the API covers — MongoDB writes are unvalidated, unaudited,
unsupported by Ubiquiti, and collection schemas drift across firmware versions.
"""

import asyncio
import json
import os
from urllib.parse import urlparse

import asyncssh

from .core import cfg, tool


def configured() -> bool:
    return bool(cfg("UNIFI_SSH_KEY") or cfg("UNIFI_SSH_PASSWORD"))


def _sq(s: str) -> str:
    return "'" + s.replace("'", "'\\''") + "'"


async def _run(command: str, timeout: int = 60) -> dict:
    if not configured():
        return {"error": "SSH not configured — set UNIFI_SSH_KEY (path to private key) or UNIFI_SSH_PASSWORD"}
    host = cfg("UNIFI_SSH_HOST") or urlparse(cfg("UNIFI_HOST")).hostname or ""
    if not host:
        return {"error": "No SSH host — set UNIFI_SSH_HOST or UNIFI_HOST"}
    kwargs: dict = {"host": host, "username": cfg("UNIFI_SSH_USER", "root"), "known_hosts": None}
    if cfg("UNIFI_SSH_KEY"):
        kwargs["client_keys"] = [os.path.expanduser(cfg("UNIFI_SSH_KEY"))]
    else:
        kwargs["password"] = cfg("UNIFI_SSH_PASSWORD")
    try:
        async with asyncssh.connect(**kwargs) as conn:
            r = await asyncio.wait_for(conn.run(command), timeout=timeout)
            return {"stdout": r.stdout.strip(), "stderr": r.stderr.strip(), "exit_code": r.exit_status}
    except Exception as e:
        return {"error": str(e)}


_GATED = not configured()


@tool(destructive=True, expose_mcp=not _GATED)
async def unifi_ssh_exec(command: str, timeout: int = 60) -> dict:
    """Run a shell command as root on the UniFi gateway (logs, tcpdump, ubnt-systool, set-inform...).
    Use the API tools for anything they cover; this is the escape hatch."""
    return await _run(command, timeout)


@tool(read_only=True, expose_mcp=not _GATED)
async def unifi_mongo_read(eval_js: str, timeout: int = 60) -> dict:
    """Read from the controller's MongoDB (ace). eval_js example:
    db.device.find({model:'U7P'}, {name:1, mac:1}).toArray() — collections: device, setting,
    wlanconf, networkconf, portconf. For fields the API omits; schemas drift across firmware."""
    if any(w in eval_js for w in (".update", ".insert", ".remove", ".delete", ".drop", ".save(", ".createIndex", ".renameCollection")):
        return {"error": "eval_js looks like a write — use unifi_mongo_write"}
    return await _run(f"mongo --port 27117 ace --quiet --eval {_sq(eval_js)}", timeout)


@tool(destructive=True, expose_mcp=not _GATED)
async def unifi_mongo_write(eval_js: str, confirm: bool = False, timeout: int = 60) -> dict:
    """Write to the controller's MongoDB (ace) — UNVALIDATED, unsupported by Ubiquiti; requires
    confirm=true. Changes are inert until unifi_provision pushes them to devices. Example:
    db.device.updateMany({model:'U7P'}, {$set:{'radio_table.$[r].ht':'160'}}, {arrayFilters:[{'r.radio':'na'}]})"""
    if not confirm:
        return {"error": "Refusing DB write without confirm=true. Verify the query with unifi_mongo_read first, and remember to unifi_provision afterwards."}
    return await _run(f"mongo --port 27117 ace --quiet --eval {_sq(eval_js)}", timeout)


@tool(destructive=True, expose_mcp=not _GATED)
async def unifi_provision(macs: list[str], timeout: int = 60) -> dict:
    """Queue force-provision for devices by MAC — required after every MongoDB write to apply it."""
    tasks = ", ".join(f"{{mac: {json.dumps(m.lower())}, type: 'cmd', cmd: 'force-provision', _id: new ObjectId()}}" for m in macs)
    return await _run(f"mongo --port 27117 ace --quiet --eval {_sq(f'db.task.insertMany([{tasks}])')}", timeout)
