# Week 3 Solution — Tagging, Testing, CI/CD & Docker

Summary of changes for reviewer: tagging system implementation, full test suite, CI/CD pipeline, Docker containerization, and related documentation.

---

## Tagging System

- **`backend/app/models.py`**  
  - Added models: `Tag`, `TagCreate`, `TagList`, `TagAssignment`.  
  - Extended `Prompt` with `tags` field; `PromptCreate` and `PromptUpdate` with optional `tag_ids`.  

- **`backend/app/storage.py`**  
  - Tag CRUD: `create_tag`, `get_tag`, `list_tags`, `delete_tag`.  
  - Prompt–tag associations: `attach_tags_to_prompt`, `detach_tags_from_prompt`.  
  - Cascade: deleting a tag detaches it from all prompts.  
  - Prompt create/update accepts `tag_ids`.  

- **`backend/app/utils.py`**  
  - `filter_prompts_by_tags()` with `tag_match` (`and` / `any`) and optional `collection_id`.  

- **`backend/app/api.py`**  
  - Tag endpoints: `POST /tags`, `GET /tags`, `DELETE /tags/{id}`.  
  - Prompt–tag endpoints: `POST /prompts/{id}/tags`, `DELETE /prompts/{id}/tags`.  
  - Prompts include `tags` in list/get; create/update accept `tag_ids`.  
  - Query param `tags` for filtering; `tag_match=and|any`.  
  - Tag name normalisation (lowercase, trimmed) per spec.  

- **`backend/tests/conftest.py`**  
  - `TestClientWithDeleteBody` to support DELETE with JSON body for tag detach.  

- **`backend/tests/test_tagging.py`**  
  - Tests for tag CRUD, attach/detach, prompt includes tags, filter by tags, edge cases (normalisation, duplicates, cascade).  

---

## API & Prompts

- **`backend/app/api.py`**  
  - Prompt endpoints enriched with tags; query param `tags` for filtering.  
  - Helper `_enrich_prompt_with_tags()` for list/get responses.  

- **`backend/tests/test_api.py`**  
  - Extended API tests for prompts, collections, and tag-related behaviour.  

---

## Main & Copilot

- **`backend/main.py`**  
  - Minor run/config adjustments if any.  

- **`.github/copilot-instructions.md`**  
  - Updated for tagging endpoints, conventions, and patterns.  

---

## Testing Infrastructure

- **`backend/Makefile`**  
  - Targets: `test`, `test-coverage`, `test-api`, `test-models`, `test-storage`, `test-utils`, `test-{endpoint}` (e.g. `test-list-prompts`), `install`, `run`.  

- **`backend/pytest.ini`**  
  - `testpaths`, markers for endpoints, `addopts`, deprecation warning filter.  

- **`backend/tests/test_models.py`**  
  - Pydantic model validation tests.  

- **`backend/tests/test_storage.py`**  
  - Storage layer unit tests.  

- **`backend/tests/test_utils.py`**  
  - Utils unit tests (sort, filter, search, validate, extract variables).  

- **`docs/TESTING_RULES.md`**  
  - How to run tests by endpoint or module; make targets; naming convention.  

### Code coverage

| Module          | Coverage |
|-----------------|----------|
| app/__init__.py | 100%     |
| app/api.py      | 95%      |
| app/models.py   | 100%     |
| app/storage.py  | 97%      |
| app/utils.py    | 97%      |
| **Total**       | **97%** (178 tests) |

### Run tests from terminal

From `backend/`:

```bash
make test              # All tests
make test-coverage     # All tests + coverage
make test-api          # API module only
pytest tests/test_tagging.py -v   # Tagging tests only
pytest tests/ -v -k "list_prompts"   # Single endpoint
```

Prerequisites: `pip install -r requirements.txt`.

---

## CI/CD

- **`.github/workflows/ci.yml`**  
  - Jobs: **Lint** (ruff check, ruff format on `backend/`), **Test** (pytest + coverage, upload `coverage.xml`), **Docs** (MkDocs build), **Deploy** (GitHub Pages on push to `main`).  
  - Triggers: push and PR to `main` and `develop`; `workflow_dispatch` for manual run.  
  - Concurrency cancels in-progress runs.  

- **`docs/CICD.md`**  
  - How to run the pipeline, manual trigger, local equivalent commands.  

---

## Docker

- **`backend/Dockerfile`**  
  - Python 3.11-slim; install from `requirements.txt`; run uvicorn on port 8000.  
  - Production run without `--reload`.  

- **`backend/.dockerignore`**  
  - Excludes venv, `__pycache__`, `.pytest_cache`, coverage files.  

- **`docker-compose.yml`**  
  - Backend service with volume mount (`./backend:/app`) and `--reload` for local dev.  
  - Port 8000.  

- **`docs/DOCKER.md`**  
  - Step-by-step: local dev (docker-compose), production (standalone image), distribution (build, tag, push).  

---

## Docs & Nav

- **`mkdocs.yml`**  
  - Added Docker and/or CICD to Contributing nav.  

- **`docs/COMMIT_SUMMARY.md`**  
  - Reviewer checklist of all changes in this commit.  

- **`docs/REVIEW_CHECKLIST.md`**  
  - Short checklist for CI/CD and Docker review.  

---

## What reviewers can do

- **Read** `week3_solution.md` (this file) for the summary above.  
- **Read** `docs/COMMIT_SUMMARY.md` for the full checklist.  
- **Run** tests: `cd backend && make test-coverage`.  
- **Run** Docker: `docker compose up --build` at project root.  
- **Trigger** CI: push to `main`/`develop` or use Actions → Run workflow.  
- **Open** `docs/DOCKER.md` for Docker usage.  
- **Open** `docs/CICD.md` for pipeline usage.  
