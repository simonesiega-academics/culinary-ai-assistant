# Docker Usage Guide

This guide explains how to run the project entirely with Docker, including Ollama, without installing Python environments or Ollama on the host system.

At a glance, the architecture is:

```text
+-------------------+
|      app          |
|  Python service   |
|-------------------|
| calls Ollama API  |
+---------+---------+
          |
          | http://ollama:11434
          |
+---------v---------+
|      ollama       |
|   LLM server      |
|-------------------|
| models in volume  |
|   ollama_data     |
+-------------------+
```

In practice: `app` runs your Python code and sends prompts to `ollama` over the internal Docker network (`http://ollama:11434`). Ollama handles inference, while model files are persisted in `ollama_data`, so they survive container restarts or recreations.

---

## 1) Docker files in this project

### `Dockerfile`
Builds the Python application image.

In this project it:
1. Uses `python:<version>-slim` (default `3.13`)
2. Installs system dependencies needed by the stack (`ffmpeg`, `espeak-ng`)
3. Installs Python dependencies from `requirements.txt`
4. Starts the app with `python src/main.py`

### `.dockerignore`
Excludes unnecessary files from build context for faster builds (for example `.git`, caches, local envs, `docs`, `data`).

### `docker-compose.yml`
Defines two services:
- `app`: this project
- `ollama`: Ollama server with GPU enabled (`gpus: all`)

It also defines `ollama_data` volume to persist downloaded models.

---

## 2) Architecture (how containers interact)

- `app` calls Ollama through `OLLAMA_BASE_URL=http://ollama:11434`
- `ollama` exposes API on port `11434`
- Downloaded models are stored in the Docker volume `ollama_data`.

Important:
- `OLLAMA_BASE_URL` is only a connection URL between containers
- Ollama itself comes from image `ollama/ollama:latest`
- Models (for example `gemma3:4b`) are downloaded separately via `ollama pull`

---

## 3) Prerequisites

- Docker Desktop installed and running
- Terminal opened in project root
- For NVIDIA GPU acceleration (RTX 4070 SUPER):
  - Updated NVIDIA driver on host
  - Docker Desktop with GPU support enabled

Quick check:

```bash
docker --version
docker compose version
docker info
```

If `docker info` fails, Docker engine is not running.

---

## 4) First-time startup (recommended)

Start Ollama first:

```bash
docker compose up --build -d ollama
```

Pull model inside Ollama container:

```bash
docker compose exec ollama ollama pull gemma3:4b
```

Run the app:

```bash
docker compose up app
```

View logs:

```bash
docker compose logs -f app
docker compose logs -f ollama
```

---

## 5) Standard daily workflow

Build and start everything:

```bash
docker compose up --build
```

Run again without rebuild:

```bash
docker compose up
```

Run in detached mode:

```bash
docker compose up -d
```

Stop services:

```bash
docker compose down
```

---

## 6) GPU checks and model management

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

---

## 7) Image vs container vs model data

- **Image**: template built/pulled from Dockerfile or registry
- **Container**: running instance of an image
- **Volume**: persistent storage (`ollama_data`) used for model files

So even if the `ollama` container restarts, models remain in `ollama_data`.

---

## 8) Cleanup and disk space management

Stop and remove containers/networks:

```bash
docker compose down
```

Stop and remove containers + volumes (also deletes Ollama models):

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

## 9) Customizing Python version

`Dockerfile` supports build arg `PYTHON_VERSION`.

Current compose default is:

```yaml
args:
  PYTHON_VERSION: "3.13"
```

To change Python version, edit `docker-compose.yml` under `services.app.build.args`.

---

## 10) Useful troubleshooting

### App cannot connect to Ollama
Cause: Ollama not started yet.

Fix:
1. `docker compose up -d ollama`
2. Wait a few seconds
3. `docker compose up app`

### Error: model not found
Cause: model was not pulled.

Fix:

```bash
docker compose exec ollama ollama pull gemma3:4b
```

### GPU not used
Possible causes:
- host driver issue
- Docker GPU support not available

Checks:

```bash
docker compose config
docker compose exec ollama ollama ps
```

### Disk usage too high
Remove unused models and cleanup:

```bash
docker compose exec ollama ollama list
docker compose exec ollama ollama rm <model_name>
docker system df
```

---

## 11) Share with other users

### Option A: Share source code
Other users run:

```bash
docker compose up --build -d ollama
docker compose exec ollama ollama pull gemma3:4b
docker compose up app
```

### Option B: Publish app image
You can publish your `app` image, but users still need an Ollama service and model pull unless you provide a custom Ollama image strategy.

---

## 12) Quick command cheat sheet

```bash
# Validate compose file
docker compose config

# Build and start all
docker compose up --build

# Start only Ollama in background
docker compose up -d ollama

# Pull model
docker compose exec ollama ollama pull gemma3:4b

# Run app
docker compose up app

# Follow logs
docker compose logs -f app
docker compose logs -f ollama

# Stop and cleanup
docker compose down

# Full reset (also deletes models)
docker compose down -v
```
