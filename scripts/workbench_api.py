#!/usr/bin/env python3
"""Compatibility wrapper for the repository workbench adapter."""

from __future__ import annotations

import subprocess

try:
    from workbench.common import ACTION_COMMANDS, JSONL_REGISTRIES, json_ready, read_jsonl
    from workbench.repository import WorkbenchRepository
    from workbench.server import build_parser, main, make_handler, route_request
except ModuleNotFoundError:
    from scripts.workbench.common import ACTION_COMMANDS, JSONL_REGISTRIES, json_ready, read_jsonl
    from scripts.workbench.repository import WorkbenchRepository
    from scripts.workbench.server import build_parser, main, make_handler, route_request

if __name__ == "__main__":
    raise SystemExit(main())
