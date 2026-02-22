# Commit Summary — Reviewer Checklist

All items covered in this commit (from `git status`).

---

## Tagging System

- [ ] **models.py** — Tag, TagCreate, TagList, TagAssignment models; Prompt has `tags` field
- [ ] **storage.py** — Tag CRUD; prompt–tag associations (attach/detach); cascade delete
- [ ] **utils.py** — `filter_prompts_by_tags()`
- [ ] **api.py** — POST /tags, GET /tags, DELETE /tags/{id}; POST /prompts/{id}/tags, DELETE /prompts/{id}/tags; `tags` in list/get prompt responses; `tag_ids` in create/update prompt; tag name normalisation
- [ ] **conftest.py** — TestClientWithDeleteBody for DELETE with JSON body
- [ ] **test_tagging.py** — Tests for tag CRUD, attach/detach, filter, edge cases

---

## API & Prompts

- [ ] **api.py** — Prompt endpoints enriched with tags; query param `tags` for filtering
- [ ] **test_api.py** — API tests for prompts, collections, tags

---

## Main & Copilot

- [ ] **main.py** — Run/config changes if any
- [ ] **copilot-instructions.md** — Updated for tagging, new endpoints, conventions

---

## Testing Infrastructure

- [ ] **Makefile** — Targets: test, test-coverage, test-api, test-models, test-storage, test-utils, test-{endpoint}, install, run
- [ ] **pytest.ini** — testpaths, markers for endpoints
- [ ] **test_models.py** — Model validation tests
- [ ] **test_storage.py** — Storage layer tests
- [ ] **test_utils.py** — Utils tests
- [ ] **docs/TESTING_RULES.md** — How to run tests by endpoint/module, make targets

### Code Coverage

| Module | Coverage | Tests |
|--------|----------|-------|
| app/__init__.py | 100% | — |
| app/api.py | 95% | — |
| app/models.py | 100% | — |
| app/storage.py | 97% | — |
| app/utils.py | 97% | — |
| **Total** | **97%** | **178 passed** |

### Run Tests from Terminal

From `backend/`:

```bash
# All tests (no coverage)
pytest tests/ -v

# All tests with coverage report
pytest tests/ -v --cov=app --cov-report=term-missing

# With make (activate venv first if using)
make test              # All tests
make test-coverage     # All tests + coverage
make test-api          # API module only + coverage
make test-models       # Models module only
make test-storage      # Storage module only
make test-utils        # Utils module only

# Single endpoint (e.g. list_prompts)
make test-list-prompts
# or: pytest tests/ -v -k "list_prompts" --cov=app.api --cov-report=term-missing

# Tagging tests only
pytest tests/test_tagging.py -v
```

Prerequisites: `cd backend`, `pip install -r requirements.txt`

---

## CI/CD

- [ ] **.github/workflows/ci.yml** — Lint (ruff), Test (pytest + coverage), Docs (MkDocs), Deploy (GitHub Pages on main)
- [ ] **docs/CICD.md** — How to run pipeline, manual trigger, local commands

---

## Docker

- [ ] **backend/Dockerfile** — Python 3.11-slim, uvicorn, port 8000
- [ ] **backend/.dockerignore** — venv, __pycache__, .pytest_cache, etc.
- [ ] **docker-compose.yml** — Backend service, volume mount, --reload
- [ ] **docs/DOCKER.md** — Local dev, production, distribution

---

## Docs & Nav

- [ ] **mkdocs.yml** — Docker and/or CICD added to nav
- [ ] **docs/REVIEW_CHECKLIST.md** — Reviewer checklist (if present)
