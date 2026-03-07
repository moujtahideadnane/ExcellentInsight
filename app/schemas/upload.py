import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UploadResponse(BaseModel):
    id: uuid.UUID = Field(serialization_alias="job_id")
    file_name: str
    file_size_bytes: int
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
