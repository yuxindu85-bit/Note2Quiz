# Contributing to Note2Quiz

Thanks for helping improve Note2Quiz.

## Development Setup

Backend:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest
```

Frontend:

```bash
cd frontend
npm install
npm run build
```

## Pull Request Guidelines

- Keep pull requests focused on one change.
- Add or update tests for backend behavior.
- Run `python -m compileall backend`, `pytest`, and `npm run build` before opening a PR.
- Update README documentation when setup, configuration, or user-facing behavior changes.
- Include screenshots or short recordings for meaningful UI changes.

## Code Style

- Prefer clear, typed Python functions.
- Keep FastAPI handlers small and move parsing/AI/export logic into services.
- Keep React components focused and reusable.
- Avoid hardcoded API keys or paid-service assumptions.

## Reporting Issues

When opening an issue, include:

- What you expected
- What happened
- Steps to reproduce
- Your OS, Python version, and Node version
- Any relevant logs
