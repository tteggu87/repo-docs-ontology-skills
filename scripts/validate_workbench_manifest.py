#!/usr/bin/env python3
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.intelligence_contracts import load_manifest


def _fail(message: str) -> None:
    raise SystemExit(message)


def _require(condition: bool, message: str) -> None:
    if not condition:
        _fail(message)


def _declared_routes(manifest: dict[str, Any]) -> list[tuple[str, str, str]]:
    workbench = manifest.get("workbench", {}) or {}
    routes: list[tuple[str, str, str]] = []
    for section in ("read_surfaces", "action_surfaces"):
        for row in workbench.get(section, []) or []:
            key = str(row.get("key", ""))
            method = str(row.get("method", "")).upper()
            path = str(row.get("path", "")).split("?", 1)[0]
            _require(bool(key and method and path), f"workbench route missing key/method/path in {section}")
            routes.append((key, method, path))
    return routes


def _implemented_route_matchers(server_text: str) -> tuple[set[str], set[str]]:
    exact = set(re.findall(r'path == "([^"]+)"', server_text))
    prefixes = set(re.findall(r'path\.startswith\("([^"]+)"\)', server_text))
    return exact, prefixes


def _route_declared_as_implemented(path: str, exact: set[str], prefixes: set[str]) -> bool:
    if path in exact:
        return True
    if "<" in path and ">" in path:
        prefix = path.split("<", 1)[0]
        return prefix in prefixes or any(prefix.startswith(item) or item.startswith(prefix) for item in prefixes)
    return any(path.startswith(prefix) for prefix in prefixes)


def validate(root: Path = ROOT) -> None:
    manifest = load_manifest(root, "workbench.yaml")
    server_text = (root / "scripts/workbench/server.py").read_text(encoding="utf-8")
    repository_text = (root / "scripts/workbench/repository.py").read_text(encoding="utf-8")
    exact, prefixes = _implemented_route_matchers(server_text)

    for key, method, path in _declared_routes(manifest):
        if method == "GET":
            _require(_route_declared_as_implemented(path, exact, prefixes), f"declared GET route is not implemented: {key} {path}")
        elif method == "POST":
            _require(path.startswith("/api/actions/"), f"POST route must be under /api/actions/: {key} {path}")
            _require('/api/actions/' in server_text, f"declared POST action route is not implemented: {key} {path}")
        else:
            _fail(f"unsupported workbench route method: {key} {method}")

    _require('"mode": "lexical_diagnostics"' in repository_text, "query_preview must return lexical_diagnostics mode")
    _require("# Lexical diagnostics" in repository_text, "query_preview must label output as lexical diagnostics")
    _require("not an answer draft" in repository_text, "query_preview must explicitly avoid answer draft semantics")
    _require("save-analysis is disabled in strict LLM mode" in repository_text, "save-analysis must be disabled in strict LLM mode")
    _require("llm_query(repo.root" in server_text, "LLM query route must delegate to strict llm_query workflow")
    _require("emit_selection_prompt" in server_text, "LLM query route must keep explicit selection prompt emission")
    _require("wikiconfig.json" not in server_text, "server routes must not expose wikiconfig.json directly")

    forbidden_direct_mutation_routes = [
        "/api/raw",
        "/api/warehouse/write",
        "/api/warehouse/mutate",
        "/api/config",
        "/api/wikiconfig",
    ]
    for route in forbidden_direct_mutation_routes:
        _require(route not in server_text, f"forbidden direct route exposed: {route}")

    workbench = manifest.get("workbench", {}) or {}
    mutation_policy = "\n".join(str(item) for item in workbench.get("mutation_policy", []) or [])
    _require("raw is immutable" in mutation_policy, "workbench mutation policy must keep raw immutable")
    _require("warehouse/jsonl remains canonical" in mutation_policy, "workbench mutation policy must protect warehouse/jsonl")


def main() -> int:
    validate(ROOT)
    print("OK workbench manifest")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

