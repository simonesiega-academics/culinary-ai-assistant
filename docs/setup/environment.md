# Local Development Setup

This guide describes the hybrid local development workflow used by the current
project architecture.

In this setup:

- the frontend runs locally with Next.js
- the backend runs locally as a Flask API
- MariaDB and Ollama run in Docker as support services

Current project layout:

- `frontend/`: Next.js + React + TypeScript UI
- `backend/`: Python API and orchestration layer with Agent 1 and Agent 2
- `backend/db/schema/create.sql`: MariaDB schema
- `data/raw_pdfs/`: sample input PDFs

Use this workflow if you want fast local iteration on frontend and backend code
while keeping database and LLM dependencies isolated in Docker.

At a glance, the local development architecture is:

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
| Agent 2: normalization |
| and persistence prep   |
+-----+-------------+----+
      |             |
      |             | http://localhost:11434
      |             v
      |    +--------+---------+
      |    |      ollama      |
      |    |    Dockerized    |
      |    |    LLM server    |
      |    +------------------+
      |
      | mysql://localhost:3306
      v
+------------------------+
|        mariadb         |
|    Dockerized DB       |
+------------------------+
```

The ingest flow is:

1. `frontend` uploads a PDF to `backend`
2. Agent 1 validates the file and extracts structured recipe data
3. Agent 2 converts structured output into MariaDB-ready records
4. `backend` persists the recipes and returns analysis plus persistence results

MariaDB and Ollama must remain running in Docker while the backend is executed
locally on the host machine.

## 1) Prerequisites

- Python 3.13
- Node.js 22 or later
- npm
- Docker Desktop or another Docker engine with Compose support

Verify the toolchain:

```bash
python --version
node --version
npm --version
docker --version
docker compose version
```

## 2) Clone the repository

```bash
git clone https://github.com/simonesiega-academics/culinary-ai-assistant.git
cd culinary-ai-assistant
```

## 3) Create a Python virtual environment

From the repository root:

```bash
python -m venv .venv
```

Activate it:

Windows:

```bash
.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

## 4) Install backend dependencies

```bash
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
```

## 5) Create local environment files

Backend configuration template:

Windows:

```bash
copy backend\.env.example backend\.env
```

macOS/Linux:

```bash
cp backend/.env.example backend/.env
```

Frontend configuration template:

Windows:

```bash
copy frontend\.env.example frontend\.env.local
```

macOS/Linux:

```bash
cp frontend/.env.example frontend/.env.local
```

Important notes:

- `frontend/.env.local` is read automatically by Next.js.
- Ensure `NEXT_PUBLIC_BACKEND_URL=http://localhost:8000` for local development.
- `backend/.env` is currently a reference template only.
- For local backend execution, export environment variables in your shell or
  rely on the default values defined in `backend/app/core/config.py`.
- When the backend runs outside Docker, set `DB_HOST=localhost` instead of
  `mariadb`.

## 6) Start support services with Docker

From the repository root, start MariaDB and Ollama:

```bash
docker compose up -d mariadb ollama
```

Pull the Ollama model used by Agent 1:

```bash
docker compose exec ollama ollama pull gemma3:4b
```

MariaDB loads `backend/db/schema/create.sql` only when the database volume is
created for the first time. Changing the schema file later does not update an
existing MariaDB volume automatically.

## 7) Export backend environment variables for local execution

Recommended values for a local backend connected to Dockerized support services:

Windows PowerShell:

```powershell
$env:API_HOST = "127.0.0.1"
$env:API_PORT = "8000"
$env:CORS_ORIGIN = "http://localhost:3000"
$env:OLLAMA_BASE_URL = "http://localhost:11434"
$env:OLLAMA_MODEL = "gemma3:4b"
$env:AGENT1_USE_LLM = "true"
$env:DB_HOST = "localhost"
$env:DB_PORT = "3306"
$env:DB_USER = "culinary"
$env:DB_PASSWORD = "culinary"
$env:DB_NAME = "ricettario"
$env:DB_DEFAULT_CATEGORY = "Importazione PDF"
```

macOS/Linux:

```bash
export API_HOST=127.0.0.1
export API_PORT=8000
export CORS_ORIGIN=http://localhost:3000
export OLLAMA_BASE_URL=http://localhost:11434
export OLLAMA_MODEL=gemma3:4b
export AGENT1_USE_LLM=true
export DB_HOST=localhost
export DB_PORT=3306
export DB_USER=culinary
export DB_PASSWORD=culinary
export DB_NAME=ricettario
export DB_DEFAULT_CATEGORY="Importazione PDF"
```

## 8) Start the backend locally

```bash
cd backend
python -m app.main
```

The API is available at `http://localhost:8000`.

Health check:

```bash
curl http://localhost:8000/api/v1/health
```

## 9) Start the frontend locally

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

The frontend is available at `http://localhost:3000`.

## 10) Run a quick end-to-end check

From the repository root:

```bash
curl -X POST -F "file=@data/raw_pdfs/recipes.pdf" http://localhost:8000/api/v1/agent-1/ingest
```

Expected outcome:

- `analysis.recipes` contains at least one recipe
- `persistence.persisted` is greater than `0`
- `persistence.failed` is `0`

## 11) Common issues

### Backend cannot connect to MariaDB

If the backend runs on the host and MariaDB runs in Docker, use:

- `DB_HOST=localhost`

Do not use `DB_HOST=mariadb` outside Docker Compose networking.

### Agent 1 reports model not found

Pull the model explicitly:

```bash
docker compose exec ollama ollama pull gemma3:4b
```

### Tables are missing

Reset only the MariaDB volume and recreate the support services:

```bash
docker compose down
docker volume ls
docker volume rm <your_compose_project>_mariadb_data
docker compose up -d mariadb ollama
```

Use `docker compose down -v` only if you intentionally want to reset Ollama
models too.

### You only want to test the parser without Ollama

Disable LLM usage:

- `AGENT1_USE_LLM=false`

Agent 1 will fall back to the internal parser implemented in
`backend/app/agents/agent_one.py`.
