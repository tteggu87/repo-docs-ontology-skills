#!/usr/bin/env python3
"""Build a deterministic project-share zip for external review."""

from __future__ import annotations

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "dist"
OUT_PATH = OUT_DIR / "llm-wiki-obsidian-share-review.zip"

TOP_LEVEL_INCLUDE = {
    "AGENTS.md",
    "README.md",
    "apps",
    "wikiconfig.example.json",
    "wikiconfig.json",
    "docs",
    "install_windows.bat",
    "intelligence",
    "raw",
    "run-workbench.command",
    "run_windows_workbench.bat",
    "scripts",
    "templates",
    "tests",
    "warehouse",
    "wiki",
}

SKIP_NAMES = {
    ".DS_Store",
}

SKIP_DIR_NAMES = {
    ".git",
    ".venv",
    ".pytest_cache",
    "__pycache__",
    "dist",
    "node_modules",
    "test-results",
}

SKIP_SUFFIXES = {
    ".tsbuildinfo",
}

SKIP_REL_PREFIXES = {
    ".agents/review-loop/",
    ".gstack/",
    ".omx/",
    ".obsidian/",
    "RESEARCH/",
    "insane-design/",
    "llm-wiki.zip",
    "vector/",
}

FIXED_TIMESTAMP = (2026, 1, 1, 0, 0, 0)


def should_skip(rel: Path) -> bool:
    rel_str = rel.as_posix()
    if rel.name in SKIP_NAMES or any(part in SKIP_NAMES for part in rel.parts):
        return True
    if any(part in SKIP_DIR_NAMES for part in rel.parts):
        return True
    if rel.suffix in SKIP_SUFFIXES:
        return True
    return any(rel_str == prefix.rstrip("/") or rel_str.startswith(prefix) for prefix in SKIP_REL_PREFIXES)


def iter_paths() -> list[Path]:
    selected: list[Path] = []
    for name in sorted(TOP_LEVEL_INCLUDE):
        path = ROOT / name
        if not path.exists():
            continue
        if path.is_file():
            if not should_skip(path.relative_to(ROOT)):
                selected.append(path)
            continue
        for child in sorted(path.rglob("*")):
            if child.is_dir():
                continue
            rel = child.relative_to(ROOT)
            if should_skip(rel):
                continue
            selected.append(child)
    return selected


def write_zip(paths: list[Path]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with ZipFile(OUT_PATH, "w", compression=ZIP_DEFLATED, compresslevel=9) as zf:
        for path in paths:
            rel = path.relative_to(ROOT).as_posix()
            info = ZipInfo(filename=rel, date_time=FIXED_TIMESTAMP)
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, path.read_bytes())


def main() -> int:
    paths = iter_paths()
    write_zip(paths)
    print(OUT_PATH)
    print(f"files={len(paths)}")
    print(f"bytes={OUT_PATH.stat().st_size}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
