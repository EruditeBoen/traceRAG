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
        db.close()