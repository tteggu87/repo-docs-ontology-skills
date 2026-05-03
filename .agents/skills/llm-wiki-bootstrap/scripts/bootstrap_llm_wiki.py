#!/usr/bin/env python3
"""Project-local launcher for the installed DocTology LLM Wiki bootstrap skill.

This repository tracks the DocTology skill contract under `.agents/skills/` so the
expected workflow is visible in GitHub.  The full scaffold generator is maintained
as the installed Codex skill script and may be updated independently from this
workspace.  Keep this launcher intentionally thin: it prevents a broken
project-local skill path while avoiding a second divergent copy of the generator.
"""

from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path


def candidate_scripts() -> list[Path]:
    home = Path.home()
    candidates = [
        home / ".codex" / "skills" / "llm-wiki-bootstrap" / "scripts" / "bootstrap_llm_wiki.py",
        home / ".agents" / "skills" / "llm-wiki-bootstrap" / "scripts" / "bootstrap_llm_wiki.py",
    ]
    env_path = os.environ.get("LLM_WIKI_BOOTSTRAP_SCRIPT")
    if env_path:
        candidates.insert(0, Path(env_path).expanduser())
    return candidates


def main() -> int:
    here = Path(__file__).resolve()
    for script in candidate_scripts():
        script = script.resolve()
        if script == here:
            continue
        if script.is_file():
            sys.argv[0] = str(script)
            runpy.run_path(str(script), run_name="__main__")
            return 0

    print(
        "error: installed llm-wiki-bootstrap generator was not found.\n"
        "Install or sync the Codex skill first, or set LLM_WIKI_BOOTSTRAP_SCRIPT "
        "to the full generator path.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
