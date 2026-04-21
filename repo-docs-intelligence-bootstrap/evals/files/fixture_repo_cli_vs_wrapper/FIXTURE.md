# Fixture Repo: CLI vs Wrapper

This repo has an official CLI and a still-live wrapper script.
The wrapper remains useful for operators, but it is not the canonical entrypoint.
`docs/CURRENT_STATE.md` is stale and the capability registry is out of sync with the action manifest.

Key paths:

- `pyproject.toml`
- `pkg_app/cli.py`
- `scripts/run_wrapper.py`
- `docs/CURRENT_STATE.md`
- `intelligence/manifests/actions.yaml`
- `intelligence/registry/capabilities.yaml`
