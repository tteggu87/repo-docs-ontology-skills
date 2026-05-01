from __future__ import annotations
from pathlib import Path
from .types import ProfileManifest
from scripts.intelligence_contracts import load_yaml_file


def _validate_target(target: str) -> None:
    if ":" not in target or target.count(":") != 1:
        raise ValueError(f"Invalid capability target: {target}")


def load_profiles(root: Path) -> list[ProfileManifest]:
    packs_dir = root / "intelligence" / "packs"
    manifests = []
    seen_profile: set[str] = set()
    seen_pack: set[str] = set()
    for path in sorted(packs_dir.glob("*/pack.yaml")):
        data = load_yaml_file(path)
        req = ["profile_id","pack_id","version","status","source_families","unit_kinds","observation_types","analysis_outputs","capabilities"]
        for key in req:
            if key not in data:
                raise ValueError(f"Missing {key} in {path}")
        if "analyze" in (data.get("capabilities") or {}):
            raise ValueError(f"Deprecated capabilities.analyze is not allowed in {path}; use capabilities.compile.")
        parse_target = data["capabilities"].get("parse",{}).get("python","")
        compile_target = data["capabilities"].get("compile",{}).get("python","")
        _validate_target(parse_target)
        _validate_target(compile_target)
        if data["profile_id"] in seen_profile:
            raise ValueError("Duplicate profile_id")
        if data["pack_id"] in seen_pack:
            raise ValueError("Duplicate pack_id")
        seen_profile.add(data["profile_id"])
        seen_pack.add(data["pack_id"])
        manifests.append(ProfileManifest(data["profile_id"], data["pack_id"], data["version"], data["status"], data["source_families"], data["unit_kinds"], data["observation_types"], data["analysis_outputs"], parse_target, compile_target))
    return manifests


def profile_by_family(root: Path) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for profile in load_profiles(root):
        for family in profile.source_families:
            if family in mapping:
                raise ValueError(f"Duplicate source family mapping: {family}")
            mapping[family] = profile.profile_id
    return mapping


def get_profile(root: Path, profile_id: str) -> ProfileManifest:
    for p in load_profiles(root):
        if p.profile_id == profile_id:
            return p
    raise KeyError(profile_id)
