# PromptLab backend - test commands
# Usage: make <target> (from backend/ directory)

.PHONY: test test-all test-coverage test-api test-health test-prompts test-collections
.PHONY: test-list-prompts test-get-prompt test-create-prompt test-update-prompt test-patch-prompt test-delete-prompt
.PHONY: test-list-collections test-get-collection test-create-collection test-delete-collection
.PHONY: install run

# Activate venv if it exists
VENV := . venv/bin/activate 2>/dev/null || true
PYTEST := $(VENV) && pytest

# Run all tests
test test-all:
	$(PYTEST) tests/ -v

# Run tests with coverage for entire app
test-coverage:
	$(PYTEST) tests/ -v --cov=app --cov-report=term-missing

# Run tests with coverage for a specific module (usage: make test-api)
test-api:
	$(PYTEST) tests/ -v --cov=app.api --cov-report=term-missing

test-models:
	$(PYTEST) tests/ -v --cov=app.models --cov-report=term-missing

test-storage:
	$(PYTEST) tests/ -v --cov=app.storage --cov-report=term-missing

test-utils:
	$(PYTEST) tests/ -v --cov=app.utils --cov-report=term-missing

# Run tests for a specific endpoint by function name
# Usage: make test-list-prompts, make test-get-prompt, etc.
test-list-prompts:
	$(PYTEST) tests/ -v -k "list_prompts" --cov=app.api --cov-report=term-missing

test-get-prompt:
	$(PYTEST) tests/ -v -k "get_prompt" --cov=app.api --cov-report=term-missing

test-create-prompt:
	$(PYTEST) tests/ -v -k "create_prompt" --cov=app.api --cov-report=term-missing

test-update-prompt:
	$(PYTEST) tests/ -v -k "update_prompt" --cov=app.api --cov-report=term-missing

test-patch-prompt:
	$(PYTEST) tests/ -v -k "patch_prompt" --cov=app.api --cov-report=term-missing

test-delete-prompt:
	$(PYTEST) tests/ -v -k "delete_prompt" --cov=app.api --cov-report=term-missing

test-health:
	$(PYTEST) tests/ -v -k "health" --cov=app.api --cov-report=term-missing

test-list-collections:
	$(PYTEST) tests/ -v -k "list_collections" --cov=app.api --cov-report=term-missing

test-get-collection:
	$(PYTEST) tests/ -v -k "get_collection" --cov=app.api --cov-report=term-missing

test-create-collection:
	$(PYTEST) tests/ -v -k "create_collection" --cov=app.api --cov-report=term-missing

test-delete-collection:
	$(PYTEST) tests/ -v -k "delete_collection" --cov=app.api --cov-report=term-missing

# Group tests by resource
test-prompts:
	$(PYTEST) tests/test_api.py::TestPrompts -v --cov=app.api --cov-report=term-missing

test-collections:
	$(PYTEST) tests/test_api.py::TestCollections -v --cov=app.api --cov-report=term-missing

# Generic: test any function (usage: make test-func FUNC=my_endpoint)
test-func:
	$(PYTEST) tests/ -v -k "$(FUNC)" --cov=app.api --cov-report=term-missing

install:
	pip install -r requirements.txt

run:
	python main.py
