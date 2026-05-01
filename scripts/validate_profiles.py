#!/usr/bin/env python3
import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.packs.loader import load_profiles

ALLOWED_PARSE_PREFIXES = ("scripts.ingest.adapters.",)
ALLOWED_ANALYZE_TARGETS = {"scripts.llm_compile_source:compile_source"}


def _load_families() -> set[str]:
    path = ROOT / "intelligence/manifests/source_families.yaml"
    try:
        import yaml  # type: ignore
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return {row["key"] for row in data.get("source_families", [])}
    except Exception:
        return {line.split(":",1)[1].strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip().startswith("- key:")}


def _check_target(target: str, *, allowed_prefixes: tuple[str, ...] = (), allowed_targets: set[str] | None = None):
    if ":" not in target or target.count(":") != 1:
        raise SystemExit(f"Invalid capability target format: {target}")
    module, fn = target.split(":", 1)
    if target not in (allowed_targets or set()) and not module.startswith(allowed_prefixes):
        raise SystemExit(f"Disallowed module prefix: {module}")
    mod = importlib.import_module(module)
    if not hasattr(mod, fn):
        raise SystemExit(f"Missing function target: {target}")


profiles = load_profiles(ROOT)
families = _load_families()
for p in profiles:
    for f in p.source_families:
        if f not in families:
            raise SystemExit(f"Unknown source family '{f}' in profile '{p.profile_id}'")
    for obs in p.observation_types:
        if "." not in obs:
            raise SystemExit(f"Invalid observation type: {obs}")
    _check_target(p.parse_target, allowed_prefixes=ALLOWED_PARSE_PREFIXES)
    _check_target(p.analyze_target, allowed_targets=ALLOWED_ANALYZE_TARGETS)
print(f"OK profiles={len(profiles)}")
