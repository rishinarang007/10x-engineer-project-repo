# PromptLab -- Copilot Instructions

These instructions define the coding standards, conventions, and best practices
for the PromptLab project. AI assistants and contributors should follow them
when generating or reviewing code.

---

## 1. Project Overview

PromptLab is a FastAPI-based REST API for storing, organising, and managing AI
prompt templates. The backend uses Pydantic v2 for validation and an in-memory
storage layer that can be swapped for a database.

**Tech stack:**

| Layer      | Technology                         |
|------------|------------------------------------|
| Framework  | FastAPI 0.109+                     |
| Validation | Pydantic 2.5+                      |
| Server     | Uvicorn 0.27+                      |
| Language   | Python 3.10+                       |
| Testing    | pytest 7.4+, pytest-cov, httpx     |

---

## 2. Project Coding Standards

### Python Version

- Target **Python 3.10+**. Use modern syntax (e.g. `X | Y` union types are
  acceptable, but the existing codebase uses `Optional[X]` from `typing` for
  consistency -- follow the existing style).

### Style Guide

- Follow **PEP 8** for all Python code.
- Maximum line length: **88 characters** (Black formatter default).
- Use **4 spaces** for indentation (never tabs).
- Use **double quotes** for strings by default. Single quotes are acceptable
  inside f-strings or to avoid escaping.
- Imports should be ordered: stdlib, third-party, local -- separated by blank
  lines. Use absolute imports (`from app.models import Prompt`), never relative
  imports.

### Type Hints

- **Every** function signature must include type hints for all parameters and
  the return type.
- Use `Optional[X]` (not `X | None`) to match the existing codebase style.
- Use `List`, `Dict`, `Optional` from `typing` for collection types.

### Docstrings

- **Every** module, class, and public function must have a docstring.
- Use **Google-style** docstrings with `Args:`, `Returns:`, `Raises:`, and
  `Example:` sections as appropriate.
- Module-level docstrings should describe the module's purpose in 1--3
  sentences.
- Class docstrings should include an `Attributes:` section for public and
  protected members.

```python
def my_function(name: str, count: int = 1) -> List[str]:
    """Short one-line summary.

    Longer description if needed.

    Args:
        name: Description of name.
        count: Description of count. Defaults to 1.

    Returns:
        A list of strings representing ...

    Raises:
        ValueError: If name is empty.

    Example:
        >>> my_function("hello", count=2)
        ['hello', 'hello']
    """
```

---

## 3. Preferred Patterns and Conventions

### API Layer (`app/api.py`)

- Each endpoint is a plain function decorated with `@app.get`, `@app.post`, etc.
- Always declare `response_model` on every route for automatic serialisation and
  OpenAPI docs.
- Use `status_code=201` for POST creation endpoints, `status_code=204` for
  DELETE endpoints.
- Validate referenced resources (e.g. `collection_id`) before creating or
  updating records. Return `400 Bad Request` if the reference is invalid.
- Group endpoints by resource with section-comment banners:
  ```python
  # ============== Prompt Endpoints ==============
  ```

### Models (`app/models.py`)

- Use a **Base / Create / Update / Full** pattern for each resource:
  - `PromptBase` -- shared fields (title, content, description, collection_id).
  - `PromptCreate(PromptBase)` -- request body for creation (no extra fields).
  - `PromptUpdate(BaseModel)` -- all fields optional for PUT/PATCH.
  - `Prompt(PromptBase)` -- full resource with server-generated `id`,
    `created_at`, `updated_at`.
- Every `Field(...)` must include a `description=` kwarg for OpenAPI docs.
- Use `default_factory` for generated fields (`generate_id`, `get_current_time`).
- Response wrapper models (`PromptList`, `CollectionList`) hold a list and a
  `total` count.

### Storage (`app/storage.py`)

- The storage layer is a plain Python class with simple CRUD methods.
- Methods return `Optional[T]` when a lookup may fail, and `bool` for delete
  operations.
- The global `storage` singleton is instantiated at module level.
- Storage methods must **not** raise exceptions -- they return `None` or `False`
  on missing resources. Exception handling belongs in the API layer.

### Utilities (`app/utils.py`)

- Utility functions must be **pure** -- no side effects, no mutation of inputs.
- Each function should do one thing and be independently testable.
- Keep `import` statements at the top of the file, not inside functions.

### General Patterns

- **Prefer composition over inheritance** except for the Pydantic model
  hierarchy.
- **Never mutate input arguments.** Return new objects (e.g. `sorted()` returns
  a new list).
- **Avoid global mutable state** beyond the `storage` singleton.
- Use `model_dump()` (Pydantic v2) instead of the deprecated `.dict()`.
- Use `model_copy(update=...)` for partial updates instead of manually
  reconstructing objects.

---

## 4. File Naming Conventions

### Python Files

| File              | Purpose                                          |
|-------------------|--------------------------------------------------|
| `api.py`          | All FastAPI route handlers                       |
| `models.py`       | Pydantic request/response models                 |
| `storage.py`      | Data persistence layer                           |
| `utils.py`        | Pure helper/utility functions                    |
| `main.py`         | Application entry point (Uvicorn runner)         |
| `__init__.py`     | Package marker; holds `__version__`              |
| `conftest.py`     | Shared pytest fixtures                           |
| `test_<module>.py`| Tests for a specific module (e.g. `test_api.py`) |

### Rules

- All Python files use **lowercase_snake_case**.
- Test files are prefixed with `test_` and live under `backend/tests/`.
- One module per concern -- do not mix route handlers with model definitions.

### Directory Structure

```
backend/
├── main.py
├── requirements.txt
├── app/
│   ├── __init__.py
│   ├── api.py
│   ├── models.py
│   ├── storage.py
│   └── utils.py
└── tests/
    ├── __init__.py
    ├── conftest.py
    └── test_api.py
docs/
    └── API_REFERENCE.md
.github/
    └── copilot-instructions.md
```

---

## 5. Error Handling Approach

### API Layer

- Use `fastapi.HTTPException` for all expected error responses.
- Return appropriate HTTP status codes:

  | Situation                        | Status | Detail message             |
  |----------------------------------|--------|----------------------------|
  | Resource not found               | 404    | `"Prompt not found"`       |
  | Invalid reference (e.g. bad FK)  | 400    | `"Collection not found"`   |
  | Validation failure (auto)        | 422    | Pydantic error array       |

- Always provide a human-readable `detail` string.
- Let FastAPI/Pydantic handle 422 validation errors automatically -- do **not**
  catch `ValidationError` in endpoint functions.

### Storage Layer

- **Never raise exceptions.** Return `None` for failed lookups and `False` for
  failed deletes.
- The API layer is responsible for translating `None`/`False` into HTTP errors.

### General Rules

- Do not use bare `except:` clauses. Always catch specific exception types.
- Do not silently swallow errors. Log or re-raise as appropriate.
- Validate inputs as early as possible (at the API boundary, via Pydantic).

---

## 6. Testing Requirements

### Framework and Tools

- **pytest** for test discovery and execution.
- **FastAPI `TestClient`** (backed by `httpx`) for HTTP-level integration tests.
- **pytest-cov** for coverage reporting.

### Running Tests

```bash
cd backend
pytest tests/ -v                              # verbose output
pytest tests/ -v --cov=app --cov-report=term-missing  # with coverage
```

### Test Organisation

- All tests live in `backend/tests/`.
- Shared fixtures go in `conftest.py`.
- Group tests into classes by resource (`TestHealth`, `TestPrompts`,
  `TestCollections`).
- Test file names must match `test_<module>.py`.

### Fixture Conventions

- Use `autouse=True` on the `clear_storage` fixture to reset state before and
  after every test.
- Provide reusable sample data via fixtures (`sample_prompt_data`,
  `sample_collection_data`).
- Fixtures that yield should clean up after the yield.

### What to Test

For **every** endpoint, include tests for:

1. **Happy path** -- valid input returns the correct status code and body.
2. **Not found** -- requesting a non-existent resource returns 404.
3. **Validation failure** -- invalid/missing fields return 422.
4. **Business rule violation** -- e.g. referencing a non-existent collection
   returns 400.
5. **Edge cases** -- empty lists, duplicate creates, partial updates with no
   fields, cascading deletes.

### Test Style

- Each test method should test **one behaviour**.
- Name tests descriptively: `test_<action>_<scenario>` (e.g.
  `test_get_prompt_not_found`, `test_create_prompt_invalid_collection`).
- Use `assert` statements with clear comparisons -- avoid generic
  `assertTrue`.
- Tests must be **independent** and **order-insensitive** (guaranteed by the
  `clear_storage` fixture).
- Do not use `time.sleep` in tests except when absolutely necessary to
  demonstrate timestamp differences; prefer deterministic approaches when
  possible.

### Coverage Goals

- Aim for **90%+ line coverage** on the `app/` package.
- Every public function in `utils.py` should have dedicated unit tests.
- Every API endpoint should have at least one happy-path and one error-path
  test.
