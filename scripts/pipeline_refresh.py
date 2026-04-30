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


def _run(script: str) -> dict:
    p = subprocess.run([sys.executable, str(ROOT / script)], capture_output=True, text=True)
    return {"ok": p.returncode == 0, "out": p.stdout.strip() or p.stderr.strip()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile")
    ap.add_argument("--source", required=True)
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--allow-profile-family-mismatch", action="store_true")
    args = ap.parse_args()

    vr = {"profiles": None, "registries": None}
    if args.validate:
        vr["profiles"] = _run("scripts/validate_profiles.py")
        if not vr["profiles"]["ok"]:
            print(json.dumps({"validation_result": vr}, ensure_ascii=False))
            raise SystemExit(1)

    summary = ingest_source(ROOT, args.source, args.profile, allow_profile_family_mismatch=args.allow_profile_family_mismatch)

    if args.validate:
        vr["registries"] = _run("scripts/validate_registries.py")
        if not vr["registries"]["ok"]:
            print(json.dumps({**summary, "validation_result": vr}, ensure_ascii=False))
            raise SystemExit(1)

    print(json.dumps({**summary, "validation_result": vr}, ensure_ascii=False))


if __name__ == "__main__":
    main()
