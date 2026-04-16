# DocTology

[English](README.md) | [한국어](README.ko.md)

DocTology is a public repository with two intentional layers:

1. `.agent/skills/`
   - reusable knowledge, ontology, bootstrap, and operator skills
2. a small runnable reference runtime at repo root
   - an Obsidian-first LLM Wiki CLI
   - an optional local workbench UI
   - runtime contracts under `intelligence/`

This repository is intentionally not a checked-in personal vault.
It is also not just a pure skill dump.
Think of it as:

`portable skill pack + runnable local reference runtime`

## Start Here

Choose the path that matches your goal:

- I want reusable skills and templates
  - start in `.agent/skills/`
- I want to run the public reference runtime in this repo
  - follow `Quick Start`
- I want a clean workspace for my own corpus
  - skip to `Bootstrap a Clean Workspace`

## What Is In This Repository

```text
DocTology/
├── .agent/
│   └── skills/
│       ├── lightweight-ontology-core/
│       ├── lg-ontology/
│       ├── llm-wiki-bootstrap/
│       ├── llm-wiki-ontology-ingest/
│       ├── ontology-pipeline-operator/
│       └── ...
├── apps/
│   └── workbench/
├── scripts/
├── templates/
├── intelligence/
├── wikiconfig.json
├── wikiconfig.example.json
├── run-workbench.command
├── run_windows_workbench.bat
└── install_windows.bat
```

## Why These Root Runtime Files Stay

These are intentionally committed because the reference runtime actually depends on them:

- `apps/workbench/` depends on `scripts/workbench_api.py`
- `scripts/llm_wiki.py` reads `templates/source_page_template.md`
- `scripts/incremental_ingest.py` reads `intelligence/manifests/source_families.yaml`
- `scripts/workbench/server.py` points to `intelligence/manifests/workbench.yaml`
- `scripts/workbench/repository.py` reads `wikiconfig.json`
- launcher files assume the root runtime layout

In other words, `intelligence/`, `templates/`, `scripts/`, and the launchers are not decorative docs here. They are part of the runnable reference contract.

## What Is Intentionally Excluded

Do not treat this repo as the place to commit your private runtime data:

- personal `raw/`
- personal `wiki/`
- personal `warehouse/`
- vector stores
- caches and scratch artifacts
- private Obsidian vault contents

Use the repo root as a public baseline or bootstrap source. Put your real corpus in your own workspace.

## Quick Start

This section is written for a first-time user who wants to clone the repo and make sure the shipped runtime actually works.

### Prerequisites

You need:

- Python 3
- Node.js and npm
- PyYAML for the Python runtime

### 1) Clone the repository

```bash
git clone https://github.com/tteggu87/DocTology.git
cd DocTology
```

### 2) Put the repo in safe first-run mode

The checked-in `wikiconfig.json` may point at a local OpenAI-compatible backend.
If you just want a safe first run without helper-model calls, replace it with the example file first:

macOS / Linux:

```bash
cp wikiconfig.example.json wikiconfig.json
```

Windows PowerShell:

```powershell
Copy-Item wikiconfig.example.json wikiconfig.json -Force
```

This keeps helper-model features disabled and lets you test the repo-local flow first.

### 3) Install dependencies

macOS / Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install pyyaml
npm --prefix apps/workbench ci
```

Windows:

```bat
install_windows.bat
```

### 4) Verify the empty baseline

These commands should work before you add any personal content:

```bash
python3 scripts/llm_wiki.py status
python3 scripts/workbench_api.py --route /api/workbench/summary
```

Expected behavior:

- `status` prints zero counts instead of crashing
- the workbench summary route returns JSON
- warnings such as `missing_index` or `missing_log` are normal for a fresh baseline

### 5) Start the workbench

macOS one-command launcher:

```bash
./run-workbench.command
```

What it does:

- starts the Python workbench API on `127.0.0.1:8765`
- starts the Vite frontend on `127.0.0.1:4174`
- opens the browser automatically

Linux or manual cross-platform start:

Terminal 1:

```bash
python3 scripts/workbench_api.py --serve --host 127.0.0.1 --port 8765
```

Terminal 2:

```bash
npm --prefix apps/workbench run dev -- --host 127.0.0.1 --port 4174
```

Then open:

```text
http://127.0.0.1:4174/#home
```

Windows launcher:

```bat
run_windows_workbench.bat
```

## What You Should See

When the workbench is connected to the correct repo, the home screen and summary API should reflect this repository, not some other local workspace.

Quick check:

```bash
python3 scripts/workbench_api.py --route /api/workbench/summary
```

You should see JSON with:

- `"root": "/.../DocTology"`
- low or zero counts on a fresh clone
- warnings such as `missing_index` and `missing_log` before first content is added

## Troubleshooting

### The launcher opens the wrong workspace

If you already have another workbench running on ports `4174` or `8765`, a browser tab may appear to show the wrong repo.

- the macOS launcher now checks whether the running listener belongs to this repo and restarts mismatched listeners
- if you still see unexpected data, verify the summary route:

```bash
python3 scripts/workbench_api.py --route /api/workbench/summary
```

The `root` value should point at `DocTology`.

### `ModuleNotFoundError: No module named 'yaml'`

Install PyYAML:

```bash
pip install pyyaml
```

### Workbench frontend does not start

Install frontend dependencies again:

```bash
npm --prefix apps/workbench ci
```

### I do not want helper-model calls on first run

Use the example config first:

```bash
cp wikiconfig.example.json wikiconfig.json
```

That keeps helper-model features disabled and lets you validate the repo-local baseline first.

### The repo feels empty after clone

That is expected.
This public repo is a baseline and reference runtime, not a checked-in personal corpus.
Add one test source under `raw/inbox/` and run the CLI flow below.

## First Content: Create a Minimal Source Page

The repo starts empty on purpose. The fastest way to confirm the CLI flow is to add one small raw source and register it.

macOS / Linux:

```bash
mkdir -p raw/inbox
printf 'hello doctology\n' > raw/inbox/hello.txt
python3 scripts/llm_wiki.py ingest raw/inbox/hello.txt --title "Hello Source"
python3 scripts/llm_wiki.py reindex
python3 scripts/llm_wiki.py lint
python3 scripts/llm_wiki.py status
```

Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force raw/inbox | Out-Null
Set-Content raw/inbox/hello.txt 'hello doctology'
python scripts/llm_wiki.py ingest raw/inbox/hello.txt --title "Hello Source"
python scripts/llm_wiki.py reindex
python scripts/llm_wiki.py lint
python scripts/llm_wiki.py status
```

After that you should see:

- `wiki/sources/source-<date>-hello-source.md`
- `wiki/_meta/index.md`
- `wiki/_meta/log.md`

This proves the shipped CLI, template path, and wiki metadata flow are wired correctly.

## Bootstrap a Clean Workspace

If you want to build your own real workspace instead of using the repo root directly, use the bundled bootstrap script.

### Plain wiki workspace

```bash
python3 .agent/skills/llm-wiki-bootstrap/scripts/bootstrap_llm_wiki.py ~/Documents/my-llm-wiki --profile wiki-only
```

### Wiki plus ontology starter

```bash
python3 .agent/skills/llm-wiki-bootstrap/scripts/bootstrap_llm_wiki.py ~/Documents/my-llm-wiki --profile wiki-plus-ontology
```

Use this path when you want:

- your own `raw/`, `wiki/`, and `warehouse/`
- a clean local workspace for real data
- the same architecture without turning the public repo itself into your private vault

## Included Skill Families

The exact contents may evolve, but the main shipped families are:

- `llm-wiki-bootstrap`
  - scaffold a new Obsidian-first LLM Wiki workspace
- `llm-wiki-ontology-ingest`
  - ingest sources into an existing ontology-backed wiki
- `lightweight-ontology-core`
  - maintain canonical JSONL ontology truth
- `lg-ontology`
  - add derived graph-style inspection on top of canonical truth
- `ontology-pipeline-operator`
  - operate and refresh an existing ontology/wiki pipeline

## Recommended Mental Model

Use this repo in one of two ways:

1. as a public skill-pack and reference implementation
2. as a bootstrap source for your own real workspace

Do not confuse the public baseline with the place where your private corpus should live.

## Notes

- `.agent` is the canonical portable folder name in this repo.
- `wikiconfig.example.json` is the safest default for first-time local testing.
- `intelligence/` is intentionally included because parts of the runtime read it directly.
- the workbench is optional, but the CLI and runtime contracts are not placeholders.
