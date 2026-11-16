# Contributing

Thanks for your interest. This repository is demo and learning material for the Ignite 2026 session "Many Domain Agents, One Governance Model"; it is not a production landing zone, and contributions should keep it small and reproducible.

## Ground rules

- **Never include secrets, tenant identifiers, subscription IDs or real customer data** in code, fixtures, docs or issue reports. All sample data is fictional and must stay that way.
- Security issues go through [SECURITY.md](SECURITY.md), not public issues.
- Keep the lab deployable by a stranger with one `azd up`: no manual portal steps on the critical path, no new required parameters without defaults or documentation.

## Before you open a pull request

1. Run the offline tests: `python -m pytest -q tests` and, for an app you changed, `python -m pytest -q` inside `apps/<app>/`. Lint with `ruff check agents identity scripts tests apps`.
2. If you touched Bicep, run `az bicep build --file infra/main.bicep` and `az bicep lint --file infra/main.bicep` (warnings suppressed in `bicepconfig.json` have comments explaining why). If you touched policy XML, run `python tests/check_policies.py`.
3. If you touched Python dependencies, edit the `requirements.in` file and recompile the hash-pinned `requirements.txt` with `pip-compile --generate-hashes`.
4. If you changed behaviour, update the matching README or page under `docs/`.

CI runs the same checks, plus CodeQL and dependency review. Actions are pinned to full commit SHAs; keep new workflow steps pinned the same way.

## Style

- Python 3.10+, standard library preferred in `scripts/` (the azd hooks must run before any dependencies are installed).
- Bicep modules stay narrow: one concern per module, least-privilege role assignments on single resources.
- Docs are plain Markdown; keep file and link paths relative.
