# EVIDENTIAL

EVIDENTIAL is an AI-assisted digital investigation platform for secure case management, evidence handling, audit trails, search, timelines, document processing, and investigation copilot workflows.

The project contains a FastAPI backend, a Next.js frontend, local SQLite support for quick development, optional PostgreSQL/pgvector through Docker, and a sample Karnataka Police FIR dataset import pipeline.

## Features

- Case management with imported FIR records
- Evidence and document upload workflows
- Investigation timeline and search APIs
- Dashboard and command center views
- Audit trail and authorization checks
- AI copilot, RAG, OCR, classification, correlation, translation, and entity extraction modules
- Offline-first LLM configuration with optional OpenAI or Gemini API keys
- Local SQLite development mode and Dockerized PostgreSQL mode

## Tech Stack

- Backend: FastAPI, SQLAlchemy, Pydantic, PyJWT, bcrypt
- Frontend: Next.js 14, React 18, TypeScript, Tailwind CSS
- Database: SQLite by default, PostgreSQL with pgvector in Docker
- Testing: pytest, httpx

## Project Structure

```text
EVIDENTIAL/
  ai/                       AI pipeline modules
  backend/                  FastAPI app, models, schemas, services, APIs
  data/                     Sample FIR CSV data
  evidence/                 Evidence integrity helpers
  frontend/                 Next.js frontend
  scripts/                  Utility scripts, including FIR import
  security/                 Audit and authorization helpers
  tests/                    Backend, AI, evidence, and security tests
  docker-compose.yml        PostgreSQL, backend, and frontend services
```

## Prerequisites

- Python 3.12 or compatible Python 3.x
- Node.js 18 or newer
- npm
- Docker Desktop, optional

## Environment Setup

Create a local environment file from the example:

```powershell
Copy-Item .env.example .env
```

By default, the app uses SQLite:

```env
DATABASE_URL=sqlite:///./evidential.db
LLM_PROVIDER=offline
```

For production-like use, change `SECRET_KEY` and use PostgreSQL instead of the default development values.

## Backend Setup

From the project root:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd ..
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend URLs:

- API health: `http://localhost:8000/health`
- API docs: `http://localhost:8000/api/v1/docs`
- ReDoc: `http://localhost:8000/api/v1/redoc`

On startup, the backend creates database tables and seeds demo users if they do not already exist.

## Demo Accounts

```text
Admin
Email: admin@evidential.gov.in
Password: Admin@123

Investigator
Email: officer@evidential.gov.in
Password: Officer@123
```

These credentials are for local development only.

## Frontend Setup

In another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Frontend URL:

```text
http://localhost:3000
```

The frontend expects the API at:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

## Import FIR Data

The sample file is:

```text
data/FIR_Details_500.csv
```

Run the importer from the project root after backend dependencies are installed:

```powershell
python scripts/import_firs.py
```

The import is idempotent. Because the CSV does not include an FIR number, the importer creates a stable `source_record_key` from each raw row and uses an internal case number like `SOURCE-...`.

## Docker Setup

To run PostgreSQL, backend, and frontend together:

```powershell
docker compose up --build
```

Services:

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- PostgreSQL: `localhost:5432`

Docker uses PostgreSQL with pgvector and stores uploaded files in a Docker volume.

## Testing

Run all tests from the project root:

```powershell
pytest
```

Run frontend checks:

```powershell
cd frontend
npm run build
```

## API Areas

The backend exposes versioned routes under `/api/v1`, including:

- Authentication and users
- Cases
- Documents
- Search
- Timeline
- Correlation
- Copilot
- Dashboard
- Health

## Notes

- The repository currently includes local generated/runtime files such as `evidential.db`, `backend/.venv`, and Python `__pycache__` folders. These should usually stay out of version control.
- Change the default `SECRET_KEY`, database password, and demo credentials before any real deployment.
- AI features can run in offline mode by default. Add `OPENAI_API_KEY` or `GEMINI_API_KEY` and update `LLM_PROVIDER` when enabling external providers.