# TraceRAG Repo Snapshot

Generated on: Fri May  8 21:32:29 EDT 2026

## Repo Tree
./.env.example
./Dockerfile
./README.md
./REPO_SNAPSHOT.md
./app/__init__.py
./app/core/__init__.py
./app/core/config.py
./app/db/__init__.py
./app/db/base.py
./app/db/session.py
./app/main.py
./app/models/__init__.py
./app/models/query_job.py
./app/schemas/__init__.py
./app/schemas/query.py
./app/services/__init__.py
./app/services/query_jobs.py
./app/worker/__init__.py
./app/worker/celery_app.py
./app/worker/tasks.py
./docker-compose.yml
./pytest.ini
./requirements.txt
./tests/__init__.py
./tests/conftest.py
./tests/test_health.py
./tests/test_queries_api.py
./tests/test_worker.py

## Recent Commits
55cd142 readme
de26002 first commit

## Key File Contents

### README.md
```
# TraceRAG

TraceRAG is a production-style async AI backend skeleton for query processing.

## Phase 1

Current vertical slice:

POST /queryies -> enqueue Celery job -> worker writes fake answer -> GET /queries/{job_id}

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
docker compose up --build```

### docker-compose.yml
```
services:
  api:
    build: .
    container_name: tracerag-api
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+psycopg://tracerag:tracerag@db:5432/tracerag
      REDIS_URL: redis://redis:6379/0
      APP_ENV: local
    volumes:
      - .:/app
    depends_on:
      - db
      - redis

  worker:
    build: .
    container_name: tracerag-worker
    command: celery -A app.worker.celery_app.celery_app worker --loglevel=info
    environment:
      DATABASE_URL: postgresql+psycopg://tracerag:tracerag@db:5432/tracerag
      REDIS_URL: redis://redis:6379/0
      APP_ENV: local
    volumes:
      - .:/app
    depends_on:
      - db
      - redis

  db:
    image: postgres:16
    container_name: tracerag-db
    environment:
      POSTGRES_USER: tracerag
      POSTGRES_PASSWORD: tracerag
      POSTGRES_DB: tracerag
    ports:
      - "5432:5432"
    volumes:
      - tracerag_postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7
    container_name: tracerag-redis
    ports:
      - "6379:6379"

volumes:
  tracerag_postgres_data:```

### Dockerfile
```
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]```

### requirements.txt
```
fastapi==0.115.6
uvicorn[standard]==0.34.0

celery==5.4.0
redis==5.2.1

SQLAlchemy==2.0.36
psycopg[binary]==3.2.10

pydantic==2.10.4
pydantic-settings==2.7.0

pytest==8.3.4
httpx==0.28.1```

### pytest.ini
```
[pytest]
testpaths = tests
pythonpath = .```

### .env.example
```
DATABASE_URL=postgresql+psycopg://tracerag:tracerag@db:5432/tracerag
REDIS_URL=redis://redis:6379/0
APP_ENV=local```

### app/__init__.py
```
```

### app/core/__init__.py
```
```

### app/core/config.py
```
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://tracerag:tracerag@db:5432/tracerag"
    redis_url: str = "redis://redis:6379/0"
    app_env: str = "local"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

settings = Settings()```

### app/db/__init__.py
```
```

### app/db/base.py
```
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass```

### app/db/session.py
```
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()```

### app/main.py
```
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.session import engine, get_db
from app.models import QueryJob
from app.schemas.query import QueryCreate, QueryResponse
from app.services.query_jobs import create_query_job, get_query_job
from app.worker.tasks import process_query_job


app = FastAPI(title="TraceRAG API")


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/queries", response_model=QueryResponse, status_code=202)
def submit_query(payload: QueryCreate, db: Session = Depends(get_db)) -> QueryJob:
    job = create_query_job(db, payload.question)

    process_query_job.delay(job.id)

    return job


@app.get("/queries/{job_id}", response_model=QueryResponse)
def read_query(job_id: str, db: Session = Depends(get_db)) -> QueryJob:
    job = get_query_job(db, job_id)

    if job is None:
        raise HTTPException(status_code=404, detail="Query job not found")

    return job```

### app/models/__init__.py
```
from app.models.query_job import QueryJob

__all__ = ["QueryJob"]```

### app/models/query_job.py
```
import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class QueryJob(Base):
    __tablename__ = "query_jobs"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    question: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )```

### app/schemas/__init__.py
```
```

### app/schemas/query.py
```
from datetime import datetime

from pydantic import BaseModel, Field


class QueryCreate(BaseModel):
    question: str = Field(..., min_length=1, max_length=4000)


class QueryResponse(BaseModel):
    id: str
    question: str
    status: str
    answer: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True,
    }```

### app/services/__init__.py
```
```

### app/services/query_jobs.py
```
from sqlalchemy.orm import Session

from app.models.query_job import QueryJob


def create_query_job(db: Session, question: str) -> QueryJob:
    job = QueryJob(
        question=question,
        status="queued",
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    return job


def get_query_job(db: Session, job_id: str) -> QueryJob | None:
    return db.get(QueryJob, job_id)


def mark_job_processing(db: Session, job: QueryJob) -> QueryJob:
    job.status = "processing"
    db.commit()
    db.refresh(job)
    return job


def mark_job_completed(db: Session, job: QueryJob, answer: str) -> QueryJob:
    job.status = "completed"
    job.answer = answer
    job.error_message = None

    db.commit()
    db.refresh(job)

    return job


def mark_job_failed(db: Session, job: QueryJob, error_message: str) -> QueryJob:
    job.status = "failed"
    job.error_message = error_message

    db.commit()
    db.refresh(job)

    return job```

### app/worker/__init__.py
```
```

### app/worker/celery_app.py
```
from celery import Celery

from app.core.config import settings


celery_app = Celery(
    "tracerag",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)

celery_app.autodiscover_tasks(["app.worker"])```

### app/worker/tasks.py
```
from app.db.session import SessionLocal
from app.services.query_jobs import (
    get_query_job,
    mark_job_completed,
    mark_job_failed,
    mark_job_processing,
)
from app.worker.celery_app import celery_app


@celery_app.task(name="app.worker.tasks.process_query_job")
def process_query_job(job_id: str) -> None:
    db = SessionLocal()

    try:
        job = get_query_job(db, job_id)

        if job is None:
            return

        mark_job_processing(db, job)

        fake_answer = f"Fake TraceRAG answer for: {job.question}"

        mark_job_completed(db, job, fake_answer)

    except Exception as exc:
        if "job" in locals() and job is not None:
            mark_job_failed(db, job, str(exc))
        raise

    finally:
        db.close()```

### tests/__init__.py
```
```

### tests/conftest.py
```
import pytest
from fastapi.testclient import TestClient

from app.db.base import Base
from app.db.session import engine
from app.main import app


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    yield

    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)```

### tests/test_health.py
```
def test_health_check(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}```

### tests/test_queries_api.py
```
from app.db.session import SessionLocal
from app.services.query_jobs import get_query_job


def test_post_query_creates_queued_job(client):
    response = client.post(
        "/queries",
        json={"question": "What is TraceRAG?"},
    )

    assert response.status_code == 202

    body = response.json()

    assert body["id"] is not None
    assert body["question"] == "What is TraceRAG?"
    assert body["status"] == "queued"
    assert body["answer"] is None

    db = SessionLocal()
    try:
        job = get_query_job(db, body["id"])
        assert job is not None
        assert job.status == "queued"
    finally:
        db.close()


def test_get_query_returns_404_for_missing_job(client):
    response = client.get("/queries/not-a-real-job-id")

    assert response.status_code == 404
    assert response.json()["detail"] == "Query job not found"```

### tests/test_worker.py
```
from app.db.session import SessionLocal
from app.services.query_jobs import create_query_job, get_query_job
from app.worker.tasks import process_query_job


def test_worker_processes_query_job():
    db = SessionLocal()

    try:
        job = create_query_job(db, "Explain async job processing.")

        process_query_job(job.id)

        updated_job = get_query_job(db, job.id)

        assert updated_job is not None
        assert updated_job.status == "completed"
        assert updated_job.answer == "Fake TraceRAG answer for: Explain async job processing."
        assert updated_job.error_message is None

    finally:
        db.close()```
