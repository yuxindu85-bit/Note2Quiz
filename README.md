# Note2Quiz

Note2Quiz is an open-source student study assistant that turns lecture files into concise summaries, quizzes, flashcards, key terms, and Markdown exports.

It is designed to run locally with optional OpenAI-compatible AI providers. If no API key is configured, the backend returns realistic mock content so the app is still usable for demos and development.

## Features

- Upload PDF, DOCX, PPTX, and TXT lecture files
- Extract readable text from uploaded files
- Generate a study summary, 10 multiple-choice questions, 20 flashcards, and key terms
- Save study packs in SQLite
- Browse previous study packs
- View results in tabs: Summary, Quiz, Flashcards, Key Terms, Original Text
- Export any study pack as Markdown
- Works without an API key through mock AI output

## Screenshots

Add screenshots here after running the app locally:

- Home upload page
- Generated study pack result tabs
- History page

## Tech Stack

- Frontend: React, Vite, TypeScript
- Backend: Python, FastAPI
- Database: SQLite
- File parsing: PyMuPDF, python-docx, python-pptx, built-in TXT parser
- AI: OpenAI-compatible chat completions API

## Setup

### 1. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env
uvicorn main:app --reload --port 8000
```

The backend will be available at `http://localhost:8000`.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:5173`.

## Environment Variables

Create a `.env` file from `.env.example`.

| Variable | Description | Default |
| --- | --- | --- |
| `AI_API_KEY` | API key for an OpenAI-compatible provider | empty, uses mock output |
| `AI_BASE_URL` | Provider base URL | `https://api.openai.com/v1` |
| `AI_MODEL` | Chat model name | `gpt-4o-mini` |
| `NOTE2QUIZ_DB_PATH` | SQLite database path | `backend/note2quiz.db` |
| `NOTE2QUIZ_UPLOAD_DIR` | Upload storage directory | `backend/uploads` |

## Supported AI Providers

Any provider that supports an OpenAI-compatible `/chat/completions` endpoint should work. Examples include:

- OpenAI
- Azure OpenAI compatible deployments
- OpenRouter
- Local OpenAI-compatible servers such as Ollama-compatible gateways or LM Studio

No API key is hardcoded. Paid services are optional and must be configured by the user.

## Tests

```bash
cd backend
pytest
```

## Roadmap

- User accounts and private libraries
- More export formats, including PDF and Anki CSV
- Better chunking for very large lecture decks
- Streaming generation progress
- Tagging and search across saved packs
- Optional local model presets

## Contributing

Contributions are welcome. Please keep changes focused, add tests for backend behavior, and update the README when setup or user-facing behavior changes.

## License

MIT. See [LICENSE](LICENSE).
