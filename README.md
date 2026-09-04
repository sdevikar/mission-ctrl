# Mission Ctrl

Intent-driven development assistant (spec-driven, intent layer for AI agents).

## Architecture

- `packages/core` (`mission_ctrl_core`): Pure Python data stores, models, validation, planner, and recap logic. Deterministic, network-free, no LLM calls.
- `packages/pi-package` (`mission_ctrl_pi`): Pi extension, hooks, and skills connecting the Pi coding agent to Mission Ctrl.

## Pi Extension Distribution Decision

- **Local Development / Dogfooding:** Pi installs local package sources directly via `pi install ./packages/pi-package` (or `pi install ./packages/pi-package -l` for project-local config). Python dependencies are managed in the environment via `uv sync --all-packages` or `pip install -e packages/core -e packages/pi-package`.
- **Remote / Production Distribution:** Pi's CLI native package manager supports `npm:<pkg>`, `git:<repo>`, and `./local/path`. Remote distribution for Pi users publishes an npm wrapper package (`npm:@mission-ctrl/pi-package`) or git repository for Pi extension discovery, while the underlying Python libraries are published to PyPI (`mission_ctrl_core` and `mission_ctrl_pi`).
