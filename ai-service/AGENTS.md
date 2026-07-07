# Repository Guidelines

## Project Structure & Module Organization

This repository is a Python 3.12 FastAPI service for TrainMindAi AI workflows. Application code lives under `app/`, with API routes in `app/api/`, settings and infrastructure in `app/core/`, SQLAlchemy models in `app/models/`, persistence code in `app/repositories/`, parsing and retrieval logic in `app/services/`, vector-store adapters in `app/vectorstore/`, and background task execution in `app/workers/`. Database migrations are in `alembic/versions/`. Tests live in `tests/` and should mirror the feature or module being exercised. Project planning notes are under `docs/superpowers/`.

## Build, Test, and Development Commands

- `uv sync`: install runtime and development dependencies from `pyproject.toml` and `uv.lock`.
- `uv run uvicorn app.main:app --reload --port 8000`: run the local API server.
- `uv run python -m app.workers.worker`: run the background worker that polls `kb_build_task`.
- `uv run alembic upgrade head --sql`: review generated DDL without touching a live database.
- `uv run alembic upgrade head`: apply migrations to the configured PostgreSQL database.
- `uv run pytest`: run the test suite.
- `uv run ruff check .` and `uv run mypy app`: run lint and type checks.

## Coding Style & Naming Conventions

Use 4-space indentation and Python type hints for new code. Ruff is configured for Python 3.12 with a 100-character line length and import sorting. Prefer explicit module names such as `task_repo.py`, `pdf_parser.py`, or `pgvector_store.py`. Keep API schemas in `app/schemas/`, database behavior in repositories, and orchestration in `app/workers/` rather than mixing layers.

## Testing Guidelines

Tests use `pytest` with `pytest-asyncio` in auto mode. Name test files `test_*.py` and test functions `test_*`. Add focused tests near the affected behavior, for example `tests/test_parsers.py` for parser changes or `tests/test_worker_handlers.py` for task pipeline changes. Run `uv run pytest`, then lint and type checks before handing off work.

## Commit & Pull Request Guidelines

Git history is not available from this checkout, so use concise, imperative commit messages with common prefixes such as `feat:`, `fix:`, `test:`, or `docs:`. Pull requests should describe the behavior change, list verification commands, call out migration or configuration impact, and link the related task or design document when applicable.

## Security & Configuration Tips

Copy `.env.example` to `.env` for local settings and never commit secrets. PostgreSQL, Redis, MinIO, and external model credentials should stay environment-driven. Alembic manages only the `ai` schema; business tables in `public` belong to the upstream backend.
