# Fixture Repo: Docs Drifted

This repo has a live service entrypoint, but the docs still center an older dev script.
The docs portal also references an impact summary that does not exist yet.
The fix should refresh current docs from code and leave an explicit impact summary behind.

Key paths:

- `service/serve.py`
- `scripts/dev_server.py`
- `docs/README.md`
- `docs/CURRENT_STATE.md`
