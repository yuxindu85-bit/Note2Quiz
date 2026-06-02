# Security Policy

## Supported Versions

The current `main` branch is the supported development version.

## Reporting a Vulnerability

Please do not open a public issue for secrets, private data exposure, or remote execution concerns. Email the maintainer or open a private security advisory on GitHub if available.

## Privacy Notes

Note2Quiz is local-first by default:

- API keys are provided through environment variables and must not be committed.
- Uploaded files are stored locally in `backend/uploads`.
- Generated study packs are stored locally in SQLite.
- Demo mode works without an AI provider key.
