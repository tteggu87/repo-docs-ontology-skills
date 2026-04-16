# Fixture Repo: Transitional Legacy Visibility

This repo has a current runtime path and a still-live legacy graph sync path.
The legacy path is no longer preferred, but it is still imported by the current runtime and must stay visible.
The current docs underreport that legacy dependency.

Key paths:

- `core/runtime.py`
- `legacy_graph/sync_edges.py`
- `docs/CURRENT_STATE.md`
