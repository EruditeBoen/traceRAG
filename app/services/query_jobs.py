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

    return job