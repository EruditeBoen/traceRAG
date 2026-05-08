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
    assert response.json()["detail"] == "Query job not found"