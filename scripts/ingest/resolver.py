from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

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
    rows = []
    try:
        import yaml  # type: ignore
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        rows = data.get("source_families", [])
    except Exception:
        cur = None
        mode = None
        in_match = False
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("- key:"):
                if cur:
                    rows.append(cur)
                cur = {"key": line.split(":", 1)[1].strip(), "match": {"path_contains": [], "extensions": []}}
                mode = None
                in_match = False
                continue
            if cur is None:
                continue
            if line.startswith("status:"):
                cur["status"] = line.split(":", 1)[1].strip()
            elif line.startswith("match:"):
                in_match = True
                mode = None
            elif in_match and line.startswith("path_contains:"):
                mode = "path_contains"
            elif in_match and line.startswith("extensions:"):
                mode = "extensions"
            elif line.startswith("default_parser:"):
                in_match = False
                mode = None
            elif line.startswith("- ") and mode:
                cur["match"][mode].append(line[2:].strip().strip("\"'"))
        if cur:
            rows.append(cur)
    rules: list[FamilyRule] = []
    for row in rows:
        match = row.get("match", {}) or {}
        rules.append(
            FamilyRule(
                key=row["key"],
                status=row.get("status", "generic"),
                path_contains=list(match.get("path_contains", []) or []),
                extensions=[x.lower() for x in (match.get("extensions", []) or [])],
            )
        )
    return rules


def _matches(rule: FamilyRule, source: Path) -> bool:
    s = source.as_posix().lower()
    suffix = source.suffix.lower()
    has_path = bool(rule.path_contains)
    has_ext = bool(rule.extensions)
    path_match = all(token.lower() in s for token in rule.path_contains) if has_path else False
    ext_match = suffix in set(rule.extensions) if has_ext else False
    if has_path and has_ext:
        return path_match and ext_match
    if has_path:
        return path_match
    if has_ext:
        return ext_match
    return False


def resolve_family(root: Path, source: Path) -> str:
    hits = [rule.key for rule in _load_source_families(root) if _matches(rule, source)]
    if len(hits) > 1:
        raise ValueError(f"Ambiguous source family: {hits}")
    if hits:
        return hits[0]
    if source.suffix.lower() in {".md", ".txt"}:
        return "generic-md-note"
    raise ValueError("No source family match")
