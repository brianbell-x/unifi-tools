"""CLI face. Every registered tool is a command: unifi_list_devices -> `unifi list devices`.

Reads and writes are prefix-separable for agent permission rules (e.g. allow `unifi list *`,
`unifi get *`). Destructive commands require --yes. JSON in (--config '{...}'), JSON out.
"""

import asyncio
import inspect
import json
import sys
from typing import get_args, get_origin

from pydantic import BaseModel

from . import __version__, api, ssh  # noqa: F401 — importing registers the tools
from .core import DESTRUCTIVE, REGISTRY, cfg, config_path, mcp


def _resolve(tokens: list[str]):
    for n in range(min(5, len(tokens)), 0, -1):
        name = "unifi_" + "_".join(t.replace("-", "_") for t in tokens[:n])
        if name in REGISTRY:
            return name, tokens[n:]
    return None, tokens


def _coerce(value: str, ann) -> object:
    if ann is bool:
        return value.lower() in ("1", "true", "yes")
    if ann is int:
        return int(value)
    if isinstance(ann, type) and issubclass(ann, BaseModel):
        return ann.model_validate(json.loads(value))
    if ann is dict or get_origin(ann) is dict:
        return json.loads(value)
    if get_origin(ann) is list:
        return json.loads(value) if value.startswith("[") else value.split(",")
    if get_origin(ann) is not None:  # Optional[X] / unions: coerce by first non-None arg
        inner = [a for a in get_args(ann) if a is not type(None)]
        return _coerce(value, inner[0]) if inner else value
    return value


def _params(fn) -> dict[str, inspect.Parameter]:
    return dict(inspect.signature(fn).parameters)


def _run_command(name: str, argv: list[str]) -> int:
    fn, params = REGISTRY[name], _params(REGISTRY[name])
    if "--help" in argv:
        print(inspect.getdoc(fn) or name)
        for p in params.values():
            d = "required" if p.default is p.empty else f"default {p.default!r}"
            print(f"  --{p.name.replace('_', '-')}  ({d})")
        if name in DESTRUCTIVE:
            print("  --yes  (required confirmation)")
        return 0
    kwargs, positionals, confirmed, i = {}, [], False, 0
    while i < len(argv):
        a = argv[i]
        if a == "--yes":
            confirmed = True
        elif a.startswith("--"):
            key = a[2:].replace("-", "_")
            if key not in params:
                print(f"unknown flag --{a[2:]} for `{name.removeprefix('unifi_').replace('_', ' ')}`", file=sys.stderr)
                return 2
            if params[key].annotation is bool and (i + 1 >= len(argv) or argv[i + 1].startswith("--")):
                kwargs[key] = True
            else:
                i += 1
                kwargs[key] = _coerce(argv[i], params[key].annotation)
        else:
            positionals.append(a)
        i += 1
    for p in params.values():
        if p.name in kwargs or not positionals:
            continue
        if get_origin(p.annotation) is list:
            kwargs[p.name] = [_coerce(v, get_args(p.annotation)[0]) for v in positionals]
            positionals = []
        else:
            kwargs[p.name] = _coerce(positionals.pop(0), p.annotation)
    if name in DESTRUCTIVE and not confirmed:
        print(json.dumps({"error": f"Destructive command — re-run with --yes: unifi {name.removeprefix('unifi_').replace('_', ' ')} ... --yes"}))
        return 1
    if confirmed and "confirm" in params:
        kwargs["confirm"] = True
    missing = [p.name for p in params.values() if p.default is p.empty and p.name not in kwargs]
    if missing:
        print(json.dumps({"error": f"Missing required arguments: {', '.join(missing)} (see --help)"}))
        return 2
    try:
        result = asyncio.run(fn(**kwargs))
    except Exception as e:
        result = {"error": str(e)}
    print(json.dumps(result, indent=2, default=str))
    return 1 if isinstance(result, dict) and "error" in result else 0


def _init(argv: list[str]) -> int:
    flags = {argv[i][2:].replace("-", "_"): argv[i + 1] for i in range(0, len(argv) - 1, 2) if argv[i].startswith("--")}
    if flags:  # non-interactive
        values = {
            "UNIFI_HOST": flags.get("host", ""),
            "UNIFI_API_KEY": flags.get("api_key", ""),
            "UNIFI_SITE_ID": flags.get("site_id", ""),
            "UNIFI_SSH_KEY": flags.get("ssh_key", ""),
            "UNIFI_SSH_PASSWORD": flags.get("ssh_password", ""),
        }
    else:
        values = {
            "UNIFI_HOST": input("Controller URL (e.g. https://192.168.1.1): ").strip(),
            "UNIFI_API_KEY": input("API key (UniFi Network > Settings > Control Plane > Integrations > Create API Key): ").strip(),
            "UNIFI_SSH_PASSWORD": input("Gateway SSH password (optional, enables the SSH escape hatch — Enter to skip): ").strip(),
        }
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({k: v for k, v in values.items() if v}, indent=2))
    print(f"Saved {path} — the single config location (env vars with the same names override it).")
    print("Verify with: unifi get app info")
    return 0


def _usage() -> int:
    groups: dict[str, list[str]] = {}
    for n in sorted(REGISTRY):
        cmd = n.removeprefix("unifi_")
        groups.setdefault(cmd.split("_")[0], []).append(cmd.replace("_", " "))
    print(f"UniFi Management Tools for AI Agents v{__version__}\n")
    print("usage: unifi <command> [args] [--flag value]    `unifi <command> --help` for details")
    print("       unifi init [--host URL --api-key KEY] [--site-id ID] [--ssh-password PW | --ssh-key PATH]")
    print("       unifi mcp                                              serve all tools over MCP (stdio)\n")
    for verb in ("list", "get", "create", "update", "set", "delete", "adopt", "remove", "restart", "power", "authorize", "unauthorize", "bulk", "ssh", "mongo", "provision"):
        if verb in groups:
            print(f"  {verb + ':':<13}" + " | ".join(c.removeprefix(verb + " ") or c for c in groups.pop(verb)))
    for verb, cmds in groups.items():
        print(f"  {verb + ':':<13}" + " | ".join(cmds))
    print("\nconfig: UNIFI_HOST, UNIFI_API_KEY, UNIFI_SITE_ID (env or `unifi init`); UNIFI_READ_ONLY=true blocks writes;")
    print("        UNIFI_VERIFY_SSL=true enforces TLS; UNIFI_SSH_KEY/UNIFI_SSH_PASSWORD enable the SSH tools.")
    return 0


def main() -> None:
    argv = sys.argv[1:]
    if not argv or argv[0] in ("--help", "-h", "help"):
        sys.exit(_usage())
    if argv[0] in ("--version", "-V"):
        print(__version__)
        sys.exit(0)
    if argv[0] == "init":
        sys.exit(_init(argv[1:]))
    if argv[0] == "mcp":
        mcp.run()
        sys.exit(0)
    name, rest = _resolve(argv)
    if not name:
        print(f"unknown command: {' '.join(argv[:3])} — run `unifi` for the command list", file=sys.stderr)
        sys.exit(2)
    sys.exit(_run_command(name, rest))


if __name__ == "__main__":
    main()
