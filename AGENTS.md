# AGENTS.md

## External File Loading

CRITICAL: When you encounter a file reference (e.g., @rules/testing.md), use your Read tool to load it on a need-to-know basis. They're relevant to the SPECIFIC task at hand.

Instructions:

- Do NOT preemptively load all references - use lazy loading based on actual need
- When loaded, treat content as mandatory instructions that override defaults
- Follow references recursively when needed

## Project overview

FastAPI backend ("PK Central API v2") serving multiple hobby project endpoints. Single Python app with modular routers, backed by MongoDB (async PyMongo). Deployed as Docker image to Docker Hub (`kinp/pk-central-v2`).

## Key commands

| Task                      | Command                                                       |
| ------------------------- | ------------------------------------------------------------- |
| Dev server                | `make dev` (runs on port 5500)                                |
| Start dev DB              | `make start-db` (Docker MongoDB on port 30017)                |
| Clear dev DB              | `make clear-db`                                               |
| Unit tests                | `make test`                                                   |
| Acceptance tests          | `make test-acc` (needs running dev DB)                        |
| All tests (local)         | `make test-all`                                               |
| All tests (Docker)        | `make test-docker` (recommended — clean env)                  |
| Clear test Docker volumes | `make clear-test-docker`                                      |
| Deploy new image          | `make deploy` (bumps `.version`, builds, pushes)              |
| Seed data                 | `make seed-init-v2 FILE=<name>` or `make seed-v1 FILE=<name>` |

**Important:** All pytest commands require `PYTHONPATH=.` — the Makefile handles this. Running `pytest` directly without it will fail with import errors.

## Architecture

- **Entry point:** `app/main.py` — creates the FastAPI app, connects to MongoDB in lifespan, includes all module routers.
- **Modules:** `app/modules/<name>/` — each module defines a FastAPI router exported as `<name>.router`. 16 modules total: activities, ai, auth, birthdays, data_backup, docs, flights, notes, personal_data, proxy, reddit, shortcuts, start_settings, strava, trips, visits.
- **Shared code:** `app/common/` — DB manager, config, auth helpers, logger, types, CRUD handler.
- **DB access:** `app.state.db` holds the async MongoDB database object, set during app lifespan startup.
- **Auth:** JWT-based with login-code flow (email). API keys also supported. AWS Cognito integration available.

## API modules

When asked to work on a new or existing module implementation read the following file for detailed guidelines: @rules/api-modules.md

## Testing

For testing strategies and coverage requirements read the following file when you receive instructions related to testing: @rules/testing.md

## Environment

- Copy `.env.example` to `.env` and fill in values. `.env` is gitignored.
- **`PK_ENV=dev`** enables the `/auth/instant-login-code` endpoint for local testing (no real email sent).
- **`ROOT_PATH`** defaults to `/central/v2` — affects all route prefixes.

## Deployment flow (`deploy.sh`)

1. Bumps patch version in `.version` (e.g. `2.1.1` → `2.1.2`)
2. Updates `docker-compose.yml` image tag
3. Builds Docker image with new version tag
4. Pushes to Docker Hub

## Conventions

- No linter, formatter, or type checker is configured. Follow existing code style (ruff would be a reasonable addition but is not present).
- No `pyproject.toml` — dependencies managed via flat `requirements.txt`.
- Python 3.13 (`.python-version`).
- Module pattern: each `app/modules/<name>/` has an `__init__.py` that re-exports the router.
