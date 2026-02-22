# Docker Guide — Step by Step

This guide explains how to run PromptLab with Docker for local development and production.

---

## Prerequisites

1. **Install Docker**
   - [Docker Desktop](https://www.docker.com/products/docker-desktop/) (macOS, Windows) includes Docker Engine and Docker Compose
   - Or install [Docker Engine](https://docs.docker.com/engine/install/) and [Docker Compose](https://docs.docker.com/compose/install/) separately on Linux

2. **Verify installation**
   ```bash
   docker --version
   docker compose version
   ```

---

## Local Development (docker-compose)

### Step 1: Go to project root

```bash
cd /path/to/10x-engineer-project-repo
```

### Step 2: Build and start services

```bash
docker compose up --build
```

- `--build` ensures the image is built from the latest code
- The backend API will be available at **http://localhost:8000**

### Step 3: Verify the API

```bash
curl http://localhost:8000/health
```

Expected response: `{"status":"healthy","version":"0.1.0"}`

### Step 4: Use hot reload

With the current setup:

- Source files in `backend/` are mounted into the container
- `--reload` is enabled, so edits to `.py` files trigger a restart automatically
- Edit code in `backend/app/` and save; the server will reload

### Step 5: Run in the background (optional)

```bash
docker compose up -d --build
```

Logs: `docker compose logs -f`

### Step 6: Stop services

```bash
docker compose down
```

---

## Production (standalone Docker)

### Step 1: Build the image

From the project root:

```bash
docker build -t promptlab-backend ./backend
```

From inside `backend/`:

```bash
cd backend
docker build -t promptlab-backend .
```

### Step 2: Run the container

```bash
docker run -p 8000:8000 promptlab-backend
```

- `-p 8000:8000` maps port 8000 from the container to the host
- No volume mount or `--reload`; suitable for production

### Step 3: Run in the background

```bash
docker run -d -p 8000:8000 --name promptlab promptlab-backend
```

### Step 4: Stop the container

```bash
docker stop promptlab
```

### Step 5: Remove the container (optional)

```bash
docker rm promptlab
```

---

## Quick Reference

| Task | Command |
|------|---------|
| **Dev: start** | `docker compose up --build` |
| **Dev: start in background** | `docker compose up -d --build` |
| **Dev: stop** | `docker compose down` |
| **Dev: view logs** | `docker compose logs -f` |
| **Prod: build** | `docker build -t promptlab-backend ./backend` |
| **Prod: run** | `docker run -p 8000:8000 promptlab-backend` |
| **Prod: run detached** | `docker run -d -p 8000:8000 --name promptlab promptlab-backend` |

---

## API Endpoints (for testing)

| Endpoint | Method | Description |
|----------|--------|-------------|
| http://localhost:8000/health | GET | Health check |
| http://localhost:8000/docs | GET | Swagger UI |
| http://localhost:8000/redoc | GET | ReDoc |

---

## Troubleshooting

### Port 8000 already in use

Stop what’s using it or map a different port:

```bash
docker run -p 8080:8000 promptlab-backend
# API at http://localhost:8080
```

With docker-compose, change `docker-compose.yml`:

```yaml
ports:
  - "8080:8000"
```

### Rebuild after dependency changes

After editing `requirements.txt`:

```bash
docker compose build --no-cache
docker compose up
```

Or with plain Docker:

```bash
docker build --no-cache -t promptlab-backend ./backend
```

### Inspect running containers

```bash
docker compose ps          # Compose services
docker ps                 # All containers
docker logs <container>   # Container logs
```
