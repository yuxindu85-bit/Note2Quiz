<p align="center">
  <strong>Note2Quiz</strong>
</p>

<p align="center">
  Turn lecture files into summaries, quizzes, flashcards, key terms, and Markdown study packs.
</p>

<p align="center">
  <img alt="MIT License" src="https://img.shields.io/badge/license-MIT-green">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.9%2B-3776AB">
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-0.115-009688">
  <img alt="React" src="https://img.shields.io/badge/React-19-61DAFB">
  <img alt="TypeScript" src="https://img.shields.io/badge/TypeScript-5-3178C6">
</p>

## Product

Note2Quiz is a local-first AI study system for students. Upload a PDF, DOCX, PPTX, or TXT lecture file and the app extracts readable text, generates a concise study summary, creates a 10-question multiple-choice quiz, builds 20 flashcards, defines configurable key terms, translates source text, creates study plans, runs exam practice, saves wrong answers, stores everything in SQLite, and exports the result as Markdown.

The project supports OpenAI-compatible APIs, but it does not require a paid AI account. If `AI_API_KEY` is missing, Note2Quiz automatically switches into demo mode with realistic mock study material.

## Features

- Upload PDF, DOCX, PPTX, and TXT files
- Extract text with PyMuPDF, python-docx, python-pptx, or a built-in TXT parser
- Generate summaries, quizzes, flashcards, and key terms
- Choose how many key terms to generate, ordered from most important downward
- Generate quizzes in importance order or randomized order
- Generate study material in English, Chinese, French, Russian, or Spanish
- Append translated source text after the original extracted text
- Save uploaded text and generated packs in SQLite
- Browse pack history and reopen saved results
- View outputs in tabs: Summary, Quiz, Flashcards, Key Terms, Original Text
- Generate 3-day, 5-day, and 7-day study plans
- Start Exam Mode from any generated quiz
- Answer one question at a time with progress and optional timer
- Save exam attempts and final scores
- Save wrong answers for targeted review
- Practice wrong questions again from the Wrong Answers page
- Export any study pack as Markdown
- Run with OpenAI-compatible APIs or free demo mode
- Clean responsive React dashboard UI
- FastAPI backend with tests and schema initialization

## Architecture

```mermaid
flowchart LR
  A["React + Vite UI"] --> B["FastAPI API"]
  B --> C["File Parser Service"]
  C --> D["Extracted Text"]
  B --> E["AI Client"]
  E --> F["OpenAI-compatible API"]
  E --> G["Demo Mock Generator"]
  B --> H["SQLite"]
  H --> I["Study Pack History"]
  H --> K["Exam Attempts + Wrong Answers"]
  H --> L["Study Plans"]
  B --> J["Markdown Export"]
```

## Screenshots

Add screenshots here after running the app:

- Home dashboard
- Upload page
- Study pack tabs
- History page
- Exam mode
- Exam review
- Wrong answers page
- Study plan tab

## Tech Stack

| Layer | Technology |
| --- | --- |
| Frontend | React, Vite, TypeScript, React Router, lucide-react |
| Backend | Python, FastAPI, Pydantic |
| Database | SQLite |
| Parsing | PyMuPDF, python-docx, python-pptx, TXT |
| AI | OpenAI-compatible `/chat/completions` |
| Tests | pytest, FastAPI TestClient |

## Installation

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env
uvicorn main:app --reload --port 8000
```

The API runs at `http://localhost:8000`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The app runs at `http://localhost:5173`.

## Environment Variables

Copy `.env.example` to `backend/.env` or project-root `.env`.

| Variable | Required | Description | Default |
| --- | --- | --- | --- |
| `AI_API_KEY` | No | API key for an OpenAI-compatible provider. Empty enables demo mode. | empty |
| `AI_BASE_URL` | No | Base URL for the provider. | `https://api.openai.com/v1` |
| `AI_MODEL` | No | Chat model name. | `gpt-4o-mini` |
| `NOTE2QUIZ_DB_PATH` | No | SQLite database path. | `backend/note2quiz.db` |
| `NOTE2QUIZ_UPLOAD_DIR` | No | Upload storage path. | `backend/uploads` |

## AI Provider Setup

Note2Quiz works with providers that expose an OpenAI-compatible chat completions endpoint.

Examples:

- OpenAI
- OpenRouter
- DeepSeek-compatible gateways
- Gemini-compatible gateways that expose OpenAI-style routes
- LM Studio or other local OpenAI-compatible servers

Example:

```bash
AI_API_KEY=sk-your-key
AI_BASE_URL=https://api.openai.com/v1
AI_MODEL=gpt-4o-mini
```

No API key is hardcoded. Users bring their own provider credentials.

## Demo Mode

If `AI_API_KEY` is not set, the backend automatically uses a local mock generator. Demo mode still exercises the full product flow:

1. Upload a file
2. Extract text
3. Generate a realistic summary
4. Create 10 quiz questions
5. Create 20 flashcards
6. Create the requested number of key terms
7. Generate study plans
8. Run an exam and save wrong answers
9. Add a demo translation preview when a non-English language is selected
10. Save the pack in SQLite
11. Export Markdown

Demo translations use a lightweight local preview so the app remains free to try. Configure an OpenAI-compatible provider for full-quality translation and multilingual generation.

This makes the project easy to evaluate without spending money.

## Exam Mode

Every generated quiz can be used as an exam. Exam Mode shows one question at a time, includes a progress indicator, supports optional timers, records selected answers, calculates the final score, and displays a review page with correct answers, wrong answers, explanations, and the final score.

Exam attempts are saved in SQLite so students can track practice history over time.

## Wrong Answer Review

Wrong answers from completed exams are saved automatically. The Wrong Answers page groups misses by study pack and shows:

- question
- user answer
- correct answer
- explanation
- source study pack

Students can jump back into Exam Mode to practice missed material again.

## Study Plan Generator

The Study Plan tab creates 3-day, 5-day, or 7-day plans from the current study pack. In demo mode, plans are generated locally from summary, flashcards, quiz items, and key terms. With an AI provider configured, this area can be extended to request richer provider-generated plans.

## API

| Method | Route | Description |
| --- | --- | --- |
| `POST` | `/api/upload` | Upload and parse a lecture file |
| `POST` | `/api/generate/{file_id}` | Generate or return the study pack for an upload |
| `GET` | `/api/packs` | List saved study packs |
| `GET` | `/api/packs/{pack_id}` | Get one study pack |
| `GET` | `/api/export/{pack_id}` | Export one pack as Markdown |
| `POST` | `/api/packs/{pack_id}/exam/start` | Start an exam attempt |
| `POST` | `/api/packs/{pack_id}/exam/submit` | Submit exam answers and save wrong answers |
| `GET` | `/api/exam-attempts` | List exam attempt history |
| `GET` | `/api/wrong-answers` | List saved wrong answers |
| `POST` | `/api/packs/{pack_id}/study-plan` | Generate or return a study plan |

## Verification

```bash
python -m compileall backend
cd backend && pytest
cd frontend && npm run build
```

## Recommended GitHub Topics

`ai`, `education`, `study-assistant`, `quiz-generator`, `flashcards`, `react`, `fastapi`, `openai`, `deepseek`, `gemini`

## Roadmap

- Add richer AI-generated study plans
- Add spaced repetition scheduling for wrong answers
- Add Anki CSV export
- Add PDF export for study packs and exam reviews
- Add local chunking for very large lecture files
- Add streaming generation progress for AI providers
- Add search and tags for saved packs
- Add Docker Compose for one-command startup
- Add GitHub Actions CI
- Add optional user accounts for hosted deployments

## Contributing

Contributions are welcome. Start with [CONTRIBUTING.md](CONTRIBUTING.md), keep changes focused, add tests for backend behavior, and include screenshots for meaningful UI changes.

## License

MIT. See [LICENSE](LICENSE).
