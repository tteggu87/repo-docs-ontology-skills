from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path

from scripts.citation import make_citation
from scripts.wiki_projection import append_log, rebuild_index, slugify, today, write_text


def now_id(prefix: str, seed: str) -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:10]
    return f"{prefix}-{stamp}-{digest}"


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def append_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    addition = "\n".join(json.dumps(row, ensure_ascii=False) for row in rows)
    path.write_text((existing.rstrip() + "\n" + addition + "\n").lstrip(), encoding="utf-8")


def units_for_profile(root: Path, profile_id: str, unit_kind: str | None = None) -> list[dict]:
    rows = [row for row in load_jsonl(root / "warehouse/jsonl/content_units.jsonl") if row.get("profile_id") == profile_id]
    if unit_kind:
        rows = [row for row in rows if row.get("unit_kind") == unit_kind]
    return rows


def tokenize(text: str) -> list[str]:
    return [token for token in re.split(r"[^0-9A-Za-z가-힣_]+", text.lower()) if len(token) >= 2]


def score_units(units: list[dict], query: str) -> list[tuple[int, dict]]:
    terms = set(tokenize(query))
    if not terms:
        return [(1, unit) for unit in units[:10]]
    scored: list[tuple[int, dict]] = []
    for unit in units:
        heading = str(unit.get("heading") or "").lower()
        text = str(unit.get("text") or "").lower()
        score = sum(3 for term in terms if term in heading) + sum(1 for term in terms if term in text)
        if score:
            scored.append((score, unit))
    return sorted(scored, key=lambda item: (-item[0], item[1].get("sequence", 0)))


def write_analysis_page(root: Path, stem: str, title: str, body: str, analysis_type: str, sources: list[str]) -> Path:
    path = root / "wiki" / "analyses" / f"{stem}.md"
    safe_title = title.replace("\\", "\\\\").replace('"', '\\"')
    safe_sources = [source.replace("\\", "\\\\").replace('"', '\\"') for source in sources]
    source_block = "sources:\n" + "\n".join(f'  - "{source}"' for source in safe_sources) if safe_sources else "sources: []"
    content = (
        "---\n"
        f'title: "{safe_title}"\n'
        "type: analysis\n"
        "status: draft\n"
        f"created: {today()}\n"
        f"updated: {today()}\n"
        f"analysis_type: {analysis_type}\n"
        f"{source_block}\n"
        "---\n\n"
        f"# {title}\n\n"
        f"{body.rstrip()}\n"
    )
    write_text(path, content)
    rebuild_index(root)
    append_log(root, "analysis", title, [f"Saved [[{path.stem}]]", f"analysis_type={analysis_type}"])
    return path


def record_analysis_run(root: Path, row: dict) -> None:
    append_jsonl(root / "warehouse/jsonl/analysis_runs.jsonl", [row])


def record_analysis_findings(root: Path, rows: list[dict]) -> None:
    if rows:
        append_jsonl(root / "warehouse/jsonl/analysis_findings.jsonl", rows)


def citation_for(root: Path, unit: dict) -> str:
    result = make_citation(root, str(unit.get("unit_id")))
    return result.get("citation") or f"`{unit.get('unit_id')}`"


def common_terms(units: list[dict], limit: int = 10) -> list[tuple[str, int]]:
    stop = {
        "the", "and", "for", "with", "that", "this", "from", "have", "will", "are", "was",
        "그리고", "그러나", "합니다", "있는", "없는", "대한", "으로", "에서", "이다", "있다",
    }
    counter: Counter[str] = Counter()
    for unit in units:
        counter.update(token for token in tokenize(str(unit.get("subject") or "")) if token not in stop)
        counter.update(token for token in tokenize(str(unit.get("heading") or "")) if token not in stop)
        counter.update(token for token in tokenize(str(unit.get("text") or "")) if token not in stop)
    return counter.most_common(limit)


def group_by(units: list[dict], key: str) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for unit in units:
        grouped[str(unit.get(key) or "unknown")].append(unit)
    return dict(grouped)
