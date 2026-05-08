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
    }