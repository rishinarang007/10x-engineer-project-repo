# PromptLab

**Your AI Prompt Engineering Platform**

[![CI](https://github.com/rishinarang007/10x-engineer-project-repo/actions/workflows/ci.yml/badge.svg)](https://github.com/rishinarang007/10x-engineer-project-repo/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/rishinarang007/10x-engineer-project-repo/branch/main/graph/badge.svg)](https://codecov.io/gh/rishinarang007/10x-engineer-project-repo)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Pydantic v2](https://img.shields.io/badge/Pydantic-v2-e92063.svg?logo=pydantic&logoColor=white)](https://docs.pydantic.dev/)
[![License](https://img.shields.io/badge/license-Internal%20%2F%20Educational-lightgrey.svg)]()
[![Version](https://img.shields.io/badge/version-0.1.0-orange.svg)]()

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

## Prerequisites

| Requirement | Version |
|-------------|---------|
| Python      | 3.10+   |
| pip         | latest  |
| Git         | latest  |

> **Optional:** Node.js 18+ if you plan to build or run a frontend client.

---

## Installation

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd 10x-engineer-project-repo

# 2. Create and activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate          # Windows

# 3. Install dependencies
cd backend
pip install -r requirements.txt
```

---

## Quick Start

```bash
# From the backend/ directory
python main.py
```

The server starts on **http://localhost:8000**.

| URL | Description |
|-----|-------------|
| http://localhost:8000/docs  | Swagger UI (interactive API explorer) |
| http://localhost:8000/redoc | ReDoc (alternative documentation)     |

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

## API Endpoint Summary

### Health

| Method | Endpoint   | Description  |
|--------|------------|--------------|
| GET    | `/health`  | Health check |

### Prompts

| Method | Endpoint              | Description                          |
|--------|-----------------------|--------------------------------------|
| GET    | `/prompts`            | List all prompts (supports query params) |
| GET    | `/prompts/{prompt_id}`| Get a single prompt by ID            |
| POST   | `/prompts`            | Create a new prompt                  |
| PUT    | `/prompts/{prompt_id}`| Full update of an existing prompt    |
| PATCH  | `/prompts/{prompt_id}`| Partial update (only provided fields)|
| DELETE | `/prompts/{prompt_id}`| Delete a prompt                      |

**Query parameters for `GET /prompts`:**

| Parameter       | Type   | Description                                  |
|-----------------|--------|----------------------------------------------|
| `collection_id` | string | Filter prompts belonging to a collection     |
| `search`        | string | Search prompts by title or description       |

### Collections

| Method | Endpoint                      | Description                |
|--------|-------------------------------|----------------------------|
| GET    | `/collections`                | List all collections       |
| GET    | `/collections/{collection_id}`| Get a single collection    |
| POST   | `/collections`                | Create a new collection    |
| DELETE | `/collections/{collection_id}`| Delete a collection and its prompts |

---

## API Examples

### Create a collection

```bash
curl -X POST http://localhost:8000/collections \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Code Review",
    "description": "Prompts for reviewing code"
  }'
```

Response (`201 Created`):

```json
{
  "name": "Code Review",
  "description": "Prompts for reviewing code",
  "id": "b3e2a1f0-...",
  "created_at": "2026-02-15T12:00:00.000000"
}
```

### Create a prompt

```bash
curl -X POST http://localhost:8000/prompts \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Review Pull Request",
    "content": "Review this pull request and provide feedback:\n\n{{code}}",
    "description": "Prompt for AI-assisted code review",
    "collection_id": "<collection-id>"
  }'
```

Response (`201 Created`):

```json
{
  "title": "Review Pull Request",
  "content": "Review this pull request and provide feedback:\n\n{{code}}",
  "description": "Prompt for AI-assisted code review",
  "collection_id": "<collection-id>",
  "id": "a1c4d7e9-...",
  "created_at": "2026-02-15T12:01:00.000000",
  "updated_at": "2026-02-15T12:01:00.000000"
}
```

### List prompts with search

```bash
curl "http://localhost:8000/prompts?search=review"
```

### Partial update (PATCH)

```bash
curl -X PATCH http://localhost:8000/prompts/<prompt-id> \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Updated description only"
  }'
```

### Delete a prompt

```bash
curl -X DELETE http://localhost:8000/prompts/<prompt-id>
```

Returns `204 No Content` on success.

---

## Development Setup

### Project Structure

```
10x-engineer-project-repo/
├── README.md
├── backend/
│   ├── main.py                # Uvicorn entry point
│   ├── requirements.txt       # Python dependencies
│   ├── app/
│   │   ├── __init__.py        # Package version
│   │   ├── api.py             # FastAPI route definitions
│   │   ├── models.py          # Pydantic request/response models
│   │   ├── storage.py         # In-memory data store
│   │   └── utils.py           # Sorting, filtering, search helpers
│   └── tests/
│       ├── conftest.py        # Pytest fixtures
│       └── test_api.py        # API integration tests
└── .gitignore
```

### Running Tests

```bash
cd backend
pytest tests/ -v
```

With coverage:

```bash
pytest tests/ -v --cov=app --cov-report=term-missing
```

### Key Dependencies

| Package   | Version | Purpose                              |
|-----------|---------|--------------------------------------|
| FastAPI   | 0.109.0 | Web framework                        |
| Uvicorn   | 0.27.0  | ASGI server                          |
| Pydantic  | 2.5.3   | Data validation and serialization    |
| pytest    | 7.4.4   | Test runner                          |
| pytest-cov| 4.1.0   | Coverage reporting                   |
| httpx     | 0.26.0  | HTTP client (used by test client)    |

### Environment Variables

No environment variables are required for local development. The server defaults to `0.0.0.0:8000`.

---

## Contributing Guidelines

1. **Fork and clone** the repository.
2. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Write clean, well-documented code.** Follow existing patterns in the codebase.
4. **Add or update tests** for any new functionality:
   ```bash
   pytest tests/ -v
   ```
5. **Ensure all tests pass** before opening a pull request.
6. **Commit with clear messages** that describe the *why*, not just the *what*:
   ```
   Add PATCH endpoint for partial prompt updates
   ```
7. **Open a pull request** against `main` with:
   - A summary of the changes
   - Any related issue numbers
   - Steps to test the changes
8. **Code review:** At least one approval is required before merging.

### Style Notes

- Follow [PEP 8](https://peps.python.org/pep-0008/) for Python code.
- Use type hints on all function signatures.
- Keep functions small and focused -- prefer composition over monoliths.
- Pydantic models go in `models.py`; route handlers go in `api.py`; helper logic goes in `utils.py`.

---

## License

This project is for internal / educational use. See the repository owner for licensing details.
