#!/usr/bin/env python3
"""HTTP routing and CLI entrypoints for the workbench adapter."""

from __future__ import annotations

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

try:
    from workbench.common import json_ready, load_json_body
    from workbench.repository import WorkbenchRepository
except ModuleNotFoundError:
    from scripts.workbench.common import json_ready, load_json_body
    from scripts.workbench.repository import WorkbenchRepository

def route_request(
    repo: WorkbenchRepository,
    method: str,
    request_target: str,
    body_text: str | None = None,
) -> tuple[int, dict[str, Any]]:
    parsed = urlparse(request_target)
    path = parsed.path
    query = parse_qs(parsed.query)

    try:
        if method == "POST" and path == "/api/actions/save-analysis":
            payload = load_json_body(body_text)
            question = str(payload.get("question", "")).strip()
            if not question:
                raise ValueError("question is required")
            limit = int(payload.get("limit", 5))
            return 200, repo.save_query_analysis(question, limit=limit)
        if method == "POST" and path == "/api/actions/review-claim":
            payload = load_json_body(body_text)
            claim_id = str(payload.get("claim_id", "")).strip()
            review_state = str(payload.get("review_state", "")).strip()
            if not claim_id:
                raise ValueError("claim_id is required")
            return 200, repo.review_claim(claim_id, review_state)
        if method == "POST" and path == "/api/actions/draft-source-summary":
            payload = load_json_body(body_text)
            source_stem = str(payload.get("source_stem", "")).strip()
            if not source_stem:
                raise ValueError("source_stem is required")
            max_chars = int(payload.get("max_chars", 12000))
            return 200, repo.draft_source_summary(source_stem, max_chars=max_chars)
        if method == "POST" and path.startswith("/api/actions/"):
            action = path.removeprefix("/api/actions/")
            return 200, repo.run_action(action)

        if method != "GET":
            return 405, {"error": "Method not allowed", "method": method}

        if path == "/api/workbench/summary":
            return 200, repo.summary()
        if path == "/api/workbench/feed":
            limit = int(query.get("limit", ["5"])[0])
            return 200, repo.workbench_feed(limit=limit)
        if path == "/api/workbench/review":
            limit = int(query.get("limit", ["5"])[0])
            return 200, repo.review_summary(limit=limit)
        if path == "/api/wiki/index":
            return 200, repo.wiki_index()
        if path.startswith("/api/wiki/related/"):
            stem = unquote(path.removeprefix("/api/wiki/related/"))
            return 200, {"stem": stem, "related_pages": repo.related_pages_for_stem(stem)}
        if path.startswith("/api/wiki/page/"):
            stem = unquote(path.removeprefix("/api/wiki/page/"))
            return 200, repo.wiki_page(stem)
        if path.startswith("/api/sources/"):
            stem = unquote(path.removeprefix("/api/sources/"))
            return 200, repo.source_detail(stem)
        if path == "/api/query/preview":
            question = query.get("q", [""])[0]
            limit = int(query.get("limit", ["5"])[0])
            return 200, repo.query_preview(question, limit=limit)
        if path == "/api/warehouse/summary":
            return 200, repo.warehouse_summary()
        if path == "/api/meta/log/recent":
            limit = int(query.get("limit", ["20"])[0])
            return 200, repo.recent_log(limit=limit)
    except FileNotFoundError as error:
        return 404, {"error": str(error)}
    except ValueError as error:
        return 400, {"error": str(error)}

    return 404, {"error": f"Unknown route: {path}"}


def make_handler(repo: WorkbenchRepository) -> type[BaseHTTPRequestHandler]:
    class WorkbenchHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            status, payload = route_request(repo, "GET", self.path)
            self._write_json(status, payload)

        def do_POST(self) -> None:  # noqa: N802
            length = int(self.headers.get("Content-Length", "0"))
            body_text = self.rfile.read(length).decode("utf-8") if length > 0 else None
            status, payload = route_request(repo, "POST", self.path, body_text=body_text)
            self._write_json(status, payload)

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
            return

        def _write_json(self, status: int, payload: dict[str, Any]) -> None:
            body = json.dumps(json_ready(payload), ensure_ascii=False, indent=2).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return WorkbenchHandler


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Python adapter for the optional repository workbench with explicit bounded actions."
    )
    parser.add_argument("--root", default=".", help="Project root to inspect. Defaults to the current directory.")
    parser.add_argument("--describe", action="store_true", help="Print the manifest path that defines the workbench contract.")
    parser.add_argument("--route", help="Render a GET route as JSON without starting a server.")
    parser.add_argument("--serve", action="store_true", help="Start the local HTTP server for adapter routes.")
    parser.add_argument("--host", default="127.0.0.1", help="Host for --serve. Defaults to 127.0.0.1.")
    parser.add_argument("--port", type=int, default=8765, help="Port for --serve. Defaults to 8765.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    repo = WorkbenchRepository(Path(args.root).resolve())

    if args.describe:
        print("See intelligence/manifests/workbench.yaml")
        return 0

    if args.route:
        status, payload = route_request(repo, "GET", args.route)
        print(json.dumps(json_ready(payload), ensure_ascii=False, indent=2))
        return 0 if status < 400 else 1

    if args.serve:
        server = ThreadingHTTPServer((args.host, args.port), make_handler(repo))
        print(f"Workbench API listening on http://{args.host}:{args.port}")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()
        return 0

    print(
        "No action selected. Use --describe, --route, or --serve.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
