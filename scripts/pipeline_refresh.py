#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.generic_ingest import ingest_source

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--profile')
    ap.add_argument('--source', required=True)
    ap.add_argument('--validate', action='store_true')
    args=ap.parse_args()
    summary=ingest_source(ROOT, args.source, args.profile)
    vr={"profiles":None,"registries":None}
    if args.validate:
        p=subprocess.run([sys.executable, str(ROOT/'scripts/validate_profiles.py')], capture_output=True, text=True)
        r=subprocess.run([sys.executable, str(ROOT/'scripts/validate_registries.py')], capture_output=True, text=True)
        vr={"profiles":{"ok":p.returncode==0,"out":p.stdout.strip() or p.stderr.strip()},"registries":{"ok":r.returncode==0,"out":r.stdout.strip() or r.stderr.strip()}}
        if p.returncode or r.returncode:
            print(json.dumps({**summary, "validation_result":vr}, ensure_ascii=False))
            raise SystemExit(1)
    print(json.dumps({**summary, "validation_result":vr}, ensure_ascii=False))

if __name__=='__main__':
    main()
