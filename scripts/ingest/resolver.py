from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass

PROFILE_BY_FAMILY = {
    "email-md-txt": "email-analysis",
    "education-md-txt": "education-analysis",
    "report-md-txt": "report-consistency-analysis",
}

@dataclass
class FamilyRule:
    key: str
    status: str
    path_contains: list[str]
    extensions: list[str]


def _load_source_families(root: Path) -> list[FamilyRule]:
    path = root / "intelligence" / "manifests" / "source_families.yaml"
    lines = path.read_text(encoding="utf-8").splitlines()
    rules: list[FamilyRule] = []
    cur: dict | None = None
    mode = None
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("- key:"):
            if cur:
                rules.append(FamilyRule(cur["key"], cur.get("status", "generic"), cur.get("path_contains", []), cur.get("extensions", [])))
            cur = {"key": line.split(":", 1)[1].strip(), "path_contains": [], "extensions": []}
            mode = None
            continue
        if cur is None:
            continue
        if line.startswith("status:"):
            cur["status"] = line.split(":", 1)[1].strip()
        elif line.startswith("path_contains:"):
            mode = "path_contains"
        elif line.startswith("extensions:"):
            mode = "extensions"
        elif line.startswith("- ") and mode:
            cur[mode].append(line[2:].strip().strip('"').strip("'"))
        else:
            mode = None
    if cur:
        rules.append(FamilyRule(cur["key"], cur.get("status", "generic"), cur.get("path_contains", []), cur.get("extensions", [])))
    return rules


def resolve_family(root: Path, source: Path) -> str:
    s = source.as_posix().lower()
    suffix = source.suffix.lower()
    hits = []
    for rule in _load_source_families(root):
        path_match = any(token.lower() in s for token in rule.path_contains) if rule.path_contains else False
        ext_match = suffix in {e.lower() for e in rule.extensions}
        if path_match or ext_match:
            hits.append(rule.key)
    if len(hits) > 1:
        raise ValueError(f"Ambiguous source family: {hits}")
    if hits:
        return hits[0]
    if suffix in {".md", ".txt"}:
        return "generic-md-note"
    raise ValueError("No source family match")
