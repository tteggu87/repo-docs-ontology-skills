from dataclasses import dataclass


@dataclass(frozen=True)
class ProfileManifest:
    profile_id: str
    pack_id: str
    version: str
    status: str
    source_families: list[str]
    unit_kinds: list[str]
    observation_types: list[str]
    analysis_outputs: list[str]
    parse_target: str
    analyze_target: str
