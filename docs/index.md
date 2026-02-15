# PromptLab

**Your AI Prompt Engineering Platform**

---

## Project Overview

PromptLab is a RESTful API platform for AI engineers to **store, organize, and manage prompts**. Think of it as a "Postman for Prompts" -- a professional workspace where individuals and teams can build, iterate on, and share prompt templates used with large language models.

The backend is built with **FastAPI** and **Pydantic**, providing a fast, type-safe, and well-documented API out of the box. Data is persisted via an in-memory storage layer that can be swapped for a production database with minimal changes.

---

## Features

- **Prompt CRUD** -- Create, read, update (full and partial), and delete prompt templates.
- **Template Variables** -- Use `{{variable}}` placeholders inside prompt content; the API can extract them automatically.
- **Collections** -- Group related prompts into named collections for better organization.
- **Search & Filter** -- Full-text search across prompt titles and descriptions, plus filtering by collection.
- **Automatic Sorting** -- Prompts are returned sorted by creation date (newest first) by default.
- **Validation** -- Pydantic models enforce field constraints (required fields, length limits) on every request.
- **Interactive API Docs** -- Auto-generated Swagger UI and ReDoc documentation at `/docs` and `/redoc`.
- **CORS Enabled** -- Allows cross-origin requests so any frontend can integrate seamlessly.

---

## Quick Start

### Prerequisites

| Requirement | Version |
|-------------|---------|
| Python      | 3.10+   |
| pip         | latest  |
| Git         | latest  |

### Installation

```bash
# Clone the repository
git clone https://github.com/rishinarang007/10x-engineer-project-repo.git
cd 10x-engineer-project-repo

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # macOS / Linux

# Install dependencies
cd backend
pip install -r requirements.txt
```

### Run the server

```bash
python main.py
```

The server starts on **http://localhost:8000**.

| URL | Description |
|-----|-------------|
| [http://localhost:8000/docs](http://localhost:8000/docs)   | Swagger UI (interactive API explorer) |
| [http://localhost:8000/redoc](http://localhost:8000/redoc) | ReDoc (alternative documentation)     |

### Verify it works

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "healthy",
  "version": "0.1.0"
}
```

---

## Documentation

| Resource | Description |
|----------|-------------|
| [API Reference](api-reference.md) | Full endpoint documentation with request/response examples |
| [Prompt Versions Spec](specs/prompt-versions.md) | Feature spec for version tracking |
| [Tagging System Spec](specs/tagging-system.md) | Feature spec for the tagging system |
| [Coding Standards](contributing/coding-standards.md) | Project conventions and contributing guidelines |

---

## Tech Stack

| Layer      | Technology                         |
|------------|------------------------------------|
| Framework  | FastAPI 0.109+                     |
| Validation | Pydantic 2.5+                      |
| Server     | Uvicorn 0.27+                      |
| Language   | Python 3.10+                       |
| Testing    | pytest 7.4+, pytest-cov, httpx     |

---

## License

This project is for internal / educational use. See the repository owner for licensing details.
