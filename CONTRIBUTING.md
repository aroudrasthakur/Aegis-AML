# Contributing to Aegis AML

This repository hosts the Cicada AML application. This guide reflects the current repo layout and development workflow.

## Development setup

### Backend

Use one virtual environment at the repository root so both `backend/` and the top-level `scripts/` directory share the same interpreter.

```bash
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -U pip
pip install -r backend/requirements.txt
copy backend\.env.example backend\.env
```

Then fill in the backend Supabase and optional OpenAI variables in `backend/.env`.

### Frontend

```bash
cd frontend
npm install
copy .env.example .env
cd ..
```

Set:

- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`
- optionally `VITE_API_PROXY_TARGET`

### Running locally

Backend:

```bash
cd backend
python -m uvicorn app.main:app --reload --reload-dir app --host 0.0.0.0 --port 8000
```

Frontend:

```bash
cd frontend
npm run dev
```

## Code style

### Python

- Lint with Ruff.
- Public functions should keep type hints.
- Keep service and repository layers small and explicit.
- Prefer updating docs when changing API routes, scoring semantics, env vars, or migrations.

Useful commands:

```bash
cd backend
python -m ruff check .
```

### TypeScript and React

- Lint with ESLint.
- Type-check with `tsc`.
- Follow existing path alias usage such as `@/api/...` and `@/components/...`.
- Reuse centralized utilities for risk tiers, run context, and formatting rather than re-implementing them in page components.

Useful commands:

```bash
cd frontend
npm run lint
npx tsc --noEmit
```

## Testing

### Backend

```bash
cd backend
python -m pytest tests -v
python -m pytest tests/test_heuristics.py -v
python -m pytest tests/test_threshold_policy.py -v
```

Areas covered today include heuristics, lenses, scoring, pipeline runs, SAR generation, storage, API routes, and regression behavior around thresholds and enrichment.

### Frontend

There is no dedicated browser test runner in this repo yet. Use type checking and linting:

```bash
cd frontend
npm run lint
npx tsc --noEmit
```

## Adding a heuristic

1. Put the heuristic in the correct module by ID range.
2. Subclass `BaseHeuristic`.
3. Define `id`, `name`, `environment`, `lens_tags`, `description`, and `data_requirements`.
4. Implement `evaluate()` and return `HeuristicResult`.
5. Register the instance so it is included in the `1..185` completeness contract.
6. Run the heuristic tests.

Current module ranges:

- `traditional.py`: `1-90`
- `blockchain.py`: `91-142`
- `hybrid.py`: `143-155` and `176-185`
- `ai_enabled.py`: `156-175`

## Adding or changing API routes

1. Update or add the router in `backend/app/api/`.
2. Use auth-scoped dependencies for run-specific routes.
3. Register the router in `backend/app/main.py` if it is new.
4. Add or update tests in `backend/tests/`.
5. Update `README.md` when route behavior or payloads change.

## Database migrations

- Add migrations in `supabase/migrations/` with the next numeric prefix.
- Keep migrations idempotent when possible.
- Document new tables or contract changes in `README.md`.

## Pull requests

1. Keep the scope tight.
2. Do not remove or rewrite unrelated user changes.
3. Include docs updates for externally visible behavior changes.
4. Make sure backend tests and frontend checks relevant to your change pass.
5. Call out any new environment variables, migrations, or model artifacts in the PR description.

## Commit messages

- Use present tense.
- Keep the subject line short.
- Mention the subsystem when helpful, for example `pipeline: keep medium-low suspicious rows`.

## Security reporting

Use GitHub issues for normal bugs. For sensitive security issues, contact the maintainer directly instead of opening a public issue.

## License

By contributing, you agree that your contributions are licensed under the MIT License.
