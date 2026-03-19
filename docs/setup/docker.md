# Docker Usage Guide

This guide explains how to run the project entirely with Docker, including
MariaDB and Ollama, without installing Python environments or Ollama directly
on the host system.

This guide covers local development with Docker Compose and is not intended as a
production deployment guide.

At a glance, the architecture is:

```text
+------------------------+
|        browser         |
|------------------------|
| accesses frontend :3000|
| accesses backend :8000 |
+-----+------------------+
      |
      |
      v
+------------------------+
|       frontend         |
|  Next.js application   |
+------------------------+

+------------------------+
|        backend         |
|   Python Flask API     |
|------------------------|
| Agent 1: PDF analysis  |
| Agent 2: DB write      |
+-----+-------------+----+
      |             |
      |             | http://ollama:11434
      |             v
      |    +--------+---------+
      |    |      ollama      |
      |    |    LLM server    |
      |    |------------------|
      |    | models in volume |
      |    |   ollama_data    |
      |    +------------------+
      |
      | mysql://mariadb:3306
      v
+------------------------+
|        mariadb         |
|    recipe database     |
|------------------------|
| schema from            |
| backend/db/schema      |
+------------------------+
```

In practice:

- `frontend` runs the user interface on port `3000`
- `backend` exposes the API on port `8000`
- `backend` calls `ollama` over the internal Docker network using
  `http://ollama:11434`
- `backend` writes recipe data to `mariadb`
- MariaDB schema initialization comes from `backend/db/schema/create.sql`
- Ollama model files are persisted in `ollama_data`, so they survive container
  restarts and recreations

The ingest flow is:

1. `frontend` uploads a PDF to `backend`
2. Agent 1 validates the upload and extracts structured recipe data
3. Agent 2 converts structured output into database-ready records
4. `backend` persists the recipes into MariaDB and returns both analysis and
   persistence results

---

## 1) Docker files in this project

### `backend/Dockerfile`

Builds the Python backend image.

In this project it:

1. Uses `python:<version>-slim` (default `3.13`)
2. Installs system packages required by the existing stack (`ffmpeg`,
   `espeak-ng`)
3. Installs Python dependencies from `backend/requirements.txt`
4. Copies the backend package into the container
5. Starts the API with `python -m app.main`

### `frontend/Dockerfile`

Builds the Next.js frontend image.

In this project it:

1. Uses `node:22-alpine`
2. Installs frontend dependencies from `frontend/package.json`
3. Copies the frontend application into the container
4. Starts the dev server on `0.0.0.0:3000`

### `.dockerignore`

Excludes unnecessary files from the Docker build context for faster and more
predictable builds.

Examples:

- `.git`
- caches and Python bytecode
- local virtual environments
- local frontend build output
- local dependency directories

### `docker-compose.yml`

Defines four services:

- `frontend`
- `backend`
- `mariadb`
- `ollama`

It also defines volumes for:

- `mariadb_data` -> persistent database storage
- `ollama_data` -> persistent Ollama models
- `frontend_node_modules` -> container-managed frontend dependencies

---

## 2) Architecture and container interaction

The service relationships are:

- browser-side requests reach the backend on `http://localhost:8000` through
  the published host port
- `backend` calls Ollama on `http://ollama:11434`
- `backend` connects to MariaDB using `DB_HOST=mariadb`
- `mariadb` initializes its schema from `backend/db/schema/create.sql`

Important details:

- `localhost` is used only from your host machine to reach published container
  ports
- `ollama` and `mariadb` are addressed by service name from inside the Docker
  network
- the backend does not need a locally installed Ollama runtime when Compose is
  used
- the frontend does not connect directly to MariaDB or Ollama

---

## 3) Runtime configuration

Runtime variables are currently defined in `docker-compose.yml`.

Important values:

- backend -> MariaDB host: `DB_HOST=mariadb`
- backend -> Ollama base URL: `OLLAMA_BASE_URL=http://ollama:11434`
- frontend -> backend base URL: `NEXT_PUBLIC_BACKEND_URL=http://localhost:8000`

Reference templates also exist in:

- `backend/.env.example`
- `frontend/.env.example`

`backend/.env.example` and `frontend/.env.example` are reference templates only;
Compose does not load them automatically via `env_file` yet.

Important frontend note:

- `NEXT_PUBLIC_BACKEND_URL=http://localhost:8000` is correct for browser
  requests issued from your host machine
- if the frontend ever performs server-side requests inside the container,
  `localhost:8000` would point back to the frontend container itself
- in that case, use the internal service address `http://backend:8000` or
  introduce a dedicated internal backend URL variable

---

## 4) Prerequisites

- Docker Desktop installed and running, or another Docker engine with Compose
  support
- terminal opened in the repository root
- optional NVIDIA GPU support if you want hardware acceleration for Ollama

Quick check:

```bash
docker --version
docker compose version
docker info
```

If `docker info` fails, the Docker engine is not running.

---

## 5) First-time startup

Build and start all services:

```bash
docker compose up --build
```

In a second terminal, pull the default model used by Agent 1:

```bash
docker compose exec ollama ollama pull gemma3:4b
```

Useful endpoints:

- frontend: `http://localhost:3000`
- backend API: `http://localhost:8000`
- backend health: `http://localhost:8000/api/v1/health`
- Ollama API: `http://localhost:11434`

Important startup note:

- on first startup, the backend container may be running before Ollama is fully
  ready or before the model has been downloaded
- in that state, the backend health endpoint can still return `200 OK` while
  ingest requests fail until the Ollama model is available

Initial verification:

```bash
curl http://localhost:8000/api/v1/health
docker compose exec ollama ollama list
```

If the containers are already built, you can start them later without the build
step:

```bash
docker compose up
```

---

## 6) Standard daily workflow

Build and start everything:

```bash
docker compose up --build
```

Start again without rebuilding:

```bash
docker compose up
```

Start in detached mode:

```bash
docker compose up -d
```

Follow logs:

```bash
docker compose logs -f frontend
docker compose logs -f backend
docker compose logs -f mariadb
docker compose logs -f ollama
```

Stop services:

```bash
docker compose down
```

---

## 7) Database initialization and persistence

The MariaDB schema is loaded automatically from:

- `backend/db/schema/create.sql`

The file is mounted into:

- `/docker-entrypoint-initdb.d/001-create.sql`

Important behavior:

- scripts in `docker-entrypoint-initdb.d` run only when the MariaDB volume is
  created for the first time
- changing the schema file alone does not reinitialize an existing database
  volume

To reset the full environment:

```bash
docker compose down -v
docker compose up --build
```

This removes:

- containers
- networks
- the MariaDB data volume
- the Ollama model volume

Use it only when you intentionally want a full reset.

Operational warning:

- `docker compose down -v` removes both the MariaDB data volume and the Ollama
  model volume
- removing `ollama_data` means the model must be downloaded again
- use `docker compose down -v` only for a full environment reset

If you only want to reset the database, remove just the MariaDB volume instead
of deleting Ollama models:

```bash
docker compose down
docker volume ls
docker volume rm <your_compose_project>_mariadb_data
docker compose up --build
```

Notes:

- the exact MariaDB volume name depends on the Compose project name
- if you are using the default project name for this repository, it is typically
  `culinary-ai-assistant_mariadb_data`

---

## 8) Verification commands

Validate the Compose file:

```bash
docker compose config
```

Check service status:

```bash
docker compose ps
```

Check the backend health endpoint:

```bash
curl http://localhost:8000/api/v1/health
```

List tables in MariaDB:

```bash
docker compose exec mariadb mariadb -uculinary -pculinary ricettario -e "SHOW TABLES;"
```

Run the full ingest pipeline against the sample PDF:

```bash
curl -X POST -F "file=@data/raw_pdfs/recipes.pdf" http://localhost:8000/api/v1/agent-1/ingest
```

Expected outcome:

- the API returns both `analysis` and `persistence`
- `persistence.persisted` is greater than `0`
- `persistence.failed` is `0`

---

## 9) GPU checks and model management

List downloaded models:

```bash
docker compose exec ollama ollama list
```

Show running model processes:

```bash
docker compose exec ollama ollama ps
```

Remove one model:

```bash
docker compose exec ollama ollama rm gemma3:4b
```

Useful note:

- if Ollama starts correctly but no GPU acceleration is used, verify Docker GPU
  support and host drivers separately

---

## 10) Image vs container vs volume

- **Image**: the built template used to create a container
- **Container**: a running instance of an image
- **Volume**: persistent storage mounted into a container

In this project:

- `culinary-ai-assistant-backend` and `culinary-ai-assistant-frontend` are image
  outputs built from the Dockerfiles
- running services are containers created from those images
- `mariadb_data` stores database files
- `ollama_data` stores downloaded LLM models

So even if `ollama` or `mariadb` containers are recreated, data survives as long
as the related volumes are not deleted.

---

## 11) Cleanup and disk usage management

Stop and remove containers and networks:

```bash
docker compose down
```

Stop and remove containers plus volumes:

```bash
docker compose down -v
```

Show Docker disk usage:

```bash
docker system df
```

Prune unused Docker resources:

```bash
docker system prune
```

Aggressive prune:

```bash
docker system prune -a
```

---

## 12) Customizing runtime behavior

### Python version

`backend/Dockerfile` supports the build argument `PYTHON_VERSION`.

Current Compose configuration:

```yaml
args:
  PYTHON_VERSION: "3.13"
```

To change it, edit `docker-compose.yml` under `services.backend.build.args`.

### Ollama model

The backend currently uses:

- `OLLAMA_MODEL=gemma3:4b`

To change the model, update the backend environment block in
`docker-compose.yml` and pull the corresponding model inside the `ollama`
container.

### Disable LLM usage temporarily

Set:

- `AGENT1_USE_LLM=false`

The backend will fall back to the internal parser in
`backend/app/agents/agent_one.py`.

---

## 13) Troubleshooting

### Backend cannot connect to Ollama

Cause:

- the `ollama` service is not ready yet
- the model has not been pulled yet

Fix:

```bash
docker compose up -d ollama
docker compose exec ollama ollama pull gemma3:4b
docker compose logs -f ollama
```

### Error: model not found

Cause:

- the configured model does not exist in `ollama_data`

Fix:

```bash
docker compose exec ollama ollama pull gemma3:4b
```

### Agent 2 fails during persistence

Cause:

- MariaDB schema is missing
- the DB volume was initialized before schema changes
- runtime data violates a database constraint

Checks:

```bash
docker compose logs -f backend
docker compose exec mariadb mariadb -uculinary -pculinary ricettario -e "SHOW TABLES;"
```

### Schema changes are not reflected

Recreate only the MariaDB volume first:

```bash
docker compose down
docker volume ls
docker volume rm <your_compose_project>_mariadb_data
docker compose up --build
```

Use `docker compose down -v` only if you intentionally want to remove Ollama
models too.

### Frontend cannot reach the backend

Confirm the backend container is running and port `8000` is published:

```bash
docker compose ps
```

Also verify that `NEXT_PUBLIC_BACKEND_URL` still points to
`http://localhost:8000` in `docker-compose.yml`.

### GPU is not used by Ollama

Possible causes:

- host driver issue
- Docker GPU support unavailable
- Ollama running correctly but falling back to CPU

Checks:

```bash
docker compose config
docker compose exec ollama ollama ps
```

---

## 14) Quick command cheat sheet

```bash
# Validate compose file
docker compose config

# Build and start all services
docker compose up --build

# Start in detached mode
docker compose up -d

# Pull the default Ollama model
docker compose exec ollama ollama pull gemma3:4b

# Follow backend logs
docker compose logs -f backend

# Check backend health
curl http://localhost:8000/api/v1/health

# Run the full ingest pipeline
curl -X POST -F "file=@data/raw_pdfs/recipes.pdf" http://localhost:8000/api/v1/agent-1/ingest

# Stop services
docker compose down

# Full reset, including database and model volumes
docker compose down -v
```
