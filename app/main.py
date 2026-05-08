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

    return job