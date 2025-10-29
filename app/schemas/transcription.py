from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class TranscriptionBase(BaseModel):
    text: str
    language: str
    duration: float

class TranscriptionCreate(TranscriptionBase):
    audio_file_id: int

class Transcription(TranscriptionBase):
    id: int
    audio_file_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True




