#!/usr/bin/env python3
import sys, importlib
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.packs.loader import load_profiles

ALLOWED_PREFIXES = ("scripts.ingest.adapters.", "scripts.analysis_profiles.")


def _load_families() -> set[str]:
    families=set()
    for line in (ROOT/"intelligence/manifests/source_families.yaml").read_text(encoding="utf-8").splitlines():
        s=line.strip()
        if s.startswith("- key:"):
            families.add(s.split(":",1)[1].strip())
    return families


def _check_target(target: str):
    if ":" not in target or target.count(":") != 1:
        raise SystemExit(f"Invalid capability target format: {target}")
    module, fn = target.split(":", 1)
    if not module.startswith(ALLOWED_PREFIXES):
        raise SystemExit(f"Disallowed module prefix: {module}")
    mod = importlib.import_module(module)
    if not hasattr(mod, fn):
        raise SystemExit(f"Missing function target: {target}")

profiles = load_profiles(ROOT)
families = _load_families()
covered_built_in = set()
for p in profiles:
    for f in p.source_families:
        if f not in families:
            raise SystemExit(f"Unknown source family '{f}' in profile '{p.profile_id}'")
        covered_built_in.add(f)
    for obs in p.observation_types:
        if "." not in obs:
            raise SystemExit(f"Invalid observation type: {obs}")
    _check_target(p.parse_target)
    _check_target(p.analyze_target)
print(f"OK profiles={len(profiles)}")
