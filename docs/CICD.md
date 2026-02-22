# CI/CD Pipeline

This document describes the GitHub Actions CI/CD pipeline and how to run it.

## Overview

The pipeline runs in `.github/workflows/ci.yml` and includes:

| Job       | Description                                      |
|-----------|--------------------------------------------------|
| **Lint**  | Runs `ruff check` and `ruff format --check`      |
| **Test**  | Runs pytest with coverage                        |
| **Docs**  | Builds MkDocs site                               |
| **Deploy**| Deploys docs to GitHub Pages (on push to main)    |

## How to Run the Pipeline

### 1. Automatic Triggers

The pipeline runs automatically on:

- **Push** to `main` or `develop`
- **Pull request** targeting `main` or `develop`

### 2. Manual Trigger

1. Open your repo on GitHub
2. Go to **Actions** tab
3. Select **"CI/CD Pipeline"** in the left sidebar
4. Click **"Run workflow"**
5. Choose branch and click **"Run workflow"**

### 3. Run Locally (Same Commands as CI)

From your terminal, run the same steps the pipeline runs:

```bash
# From project root
cd backend

# 1. Lint (install ruff first: pip install ruff)
ruff check .
ruff format --check .

# 2. Test with coverage
pip install -r requirements.txt
pytest tests/ -v --cov=app --cov-report=term-missing

# 3. Build docs (from project root)
cd ..
pip install mkdocs-material mkdocstrings[python]
mkdocs build --strict
```

### 4. Quick Commands Using Make

From `backend/`:

```bash
make install      # Install dependencies
make test         # Run all tests
make test-coverage # Run tests with full coverage
```

## Pipeline Jobs in Detail

### Lint Job

- Uses **ruff** for fast Python linting and formatting
- `continue-on-error: true` is set so builds don't fail on lint; remove when codebase is clean

### Test Job

- Python 3.11
- Installs from `backend/requirements.txt` with pip cache
- Runs pytest with coverage; uploads `coverage.xml` as artifact (7 days retention)

### Docs Job

- Builds MkDocs Material site
- Validates docs build successfully before deploy

### Deploy Docs Job

- Runs only on **push to main**
- Requires GitHub Pages to be enabled (Settings → Pages → Source: GitHub Actions)
- Deploys to `https://<user>.github.io/<repo>/`

## Enabling GitHub Pages

1. Go to **Settings** → **Pages**
2. Under **Build and deployment**:
   - Source: **GitHub Actions**
3. Save

After the first successful deploy, docs will be available at your Pages URL.
