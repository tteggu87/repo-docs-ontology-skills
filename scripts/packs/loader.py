from __future__ import annotations
from pathlib import Path
from scripts.simple_yaml import load_simple_yaml
from .types import ProfileManifest


def _validate_target(target: str) -> None:
    if ":" not in target or target.count(":") != 1:
        raise ValueError(f"Invalid capability target: {target}")


def load_profiles(root: Path) -> list[ProfileManifest]:
    packs_dir = root / "intelligence" / "packs"
    manifests = []
    seen_profile: set[str] = set()
    seen_pack: set[str] = set()
    for path in sorted(packs_dir.glob("*/pack.yaml")):
        data = load_simple_yaml(path.read_text(encoding="utf-8")) or {}
        req = ["profile_id","pack_id","version","status","source_families","unit_kinds","observation_types","analysis_outputs","capabilities"]
        for key in req:
            if key not in data:
                raise ValueError(f"Missing {key} in {path}")
        parse_target = data["capabilities"].get("parse",{}).get("python","")
        analyze_target = data["capabilities"].get("analyze",{}).get("python","")
        _validate_target(parse_target)
        _validate_target(analyze_target)
        if data["profile_id"] in seen_profile:
            raise ValueError("Duplicate profile_id")
        if data["pack_id"] in seen_pack:
            raise ValueError("Duplicate pack_id")
        seen_profile.add(data["profile_id"])
        seen_pack.add(data["pack_id"])
        manifests.append(ProfileManifest(data["profile_id"], data["pack_id"], data["version"], data["status"], data["source_families"], data["unit_kinds"], data["observation_types"], data["analysis_outputs"], parse_target, analyze_target))
    return manifests


def get_profile(root: Path, profile_id: str) -> ProfileManifest:
    for p in load_profiles(root):
        if p.profile_id == profile_id:
            return p
    raise KeyError(profile_id)
