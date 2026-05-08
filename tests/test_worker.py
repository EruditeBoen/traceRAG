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
        db.close()