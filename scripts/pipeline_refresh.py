#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.generic_ingest import ingest_source
from scripts.llm_compile_source import compile_source


def _run(script: str) -> dict:
    p = subprocess.run([sys.executable, str(ROOT / script)], capture_output=True, text=True)
    return {"ok": p.returncode == 0, "out": p.stdout.strip() or p.stderr.strip()}


def _run_args(args: list[str]) -> dict:
    p = subprocess.run(args, cwd=ROOT, capture_output=True, text=True)
    return {"ok": p.returncode == 0, "out": p.stdout.strip() or p.stderr.strip()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile")
    ap.add_argument("--source", required=True)
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--validate-full", action="store_true")
    ap.add_argument("--allow-profile-family-mismatch", action="store_true")
    ap.add_argument("--analyze", action="store_true")
    ap.add_argument("--write-analysis", action="store_true")
    ap.add_argument("--question")
    args = ap.parse_args()

    vr = {"profiles": None, "registries": None, "intelligence": None, "repo_docs_intelligence": None, "workbench_manifest": None, "pytest_smoke": None}
    if args.validate or args.validate_full:
        vr["profiles"] = _run("scripts/validate_profiles.py")
        if not vr["profiles"]["ok"]:
            print(json.dumps({"validation_result": vr}, ensure_ascii=False))
            raise SystemExit(1)
    if args.validate_full:
        for key, script in [
            ("repo_docs_intelligence", "scripts/validate_repo_docs_intelligence.py"),
            ("workbench_manifest", "scripts/validate_workbench_manifest.py"),
            ("intelligence", "scripts/validate_intelligence.py"),
        ]:
            vr[key] = _run(script)
            if not vr[key]["ok"]:
                print(json.dumps({"validation_result": vr}, ensure_ascii=False))
                raise SystemExit(1)

    summary = ingest_source(ROOT, args.source, args.profile, allow_profile_family_mismatch=args.allow_profile_family_mismatch)
    if args.analyze or args.write_analysis:
        source_pages = [path for path in summary.get("affected_wiki_paths", []) if path.startswith("wiki/sources/")]
        if source_pages:
            summary["analysis"] = compile_source(ROOT, source_pages[0])
        else:
            summary["analysis"] = {"status": "skipped", "message": "no projected source page available for LLM compile"}
        if summary.get("analysis", {}).get("proposal_path"):
            summary["analysis_output_path"] = summary["analysis"]["proposal_path"]

    if args.validate or args.validate_full:
        vr["registries"] = _run("scripts/validate_registries.py")
        if not vr["registries"]["ok"]:
            print(json.dumps({**summary, "validation_result": vr}, ensure_ascii=False))
            raise SystemExit(1)
    if args.validate_full:
        vr["pytest_smoke"] = _run_args([sys.executable, "-m", "pytest", "-q"])
        if not vr["pytest_smoke"]["ok"]:
            print(json.dumps({**summary, "validation_result": vr}, ensure_ascii=False))
            raise SystemExit(1)

    print(json.dumps({**summary, "validation_result": vr}, ensure_ascii=False))


if __name__ == "__main__":
    main()
