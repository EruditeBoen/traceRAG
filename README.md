# TraceRAG

TraceRAG is a production-style async AI backend skeleton for query processing.

## Phase 1

Current vertical slice:

POST /queries -> enqueue Celery job -> worker writes fake answer -> GET /queries/{job_id}

## Stack

- FastAPI
- Celery
- Redis
- PostgreSQL
- SQLAlchemy
- Docker Compose
- pytest

## Run locally

```bash
docker compose up --build