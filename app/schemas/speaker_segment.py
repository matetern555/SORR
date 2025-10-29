from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SpeakerSegmentBase(BaseModel):
    start_time: float
    end_time: float
    speaker_label: str
    text: Optional[str] = None
    confidence: Optional[float] = None

class SpeakerSegmentCreate(SpeakerSegmentBase):
    transcription_id: int

class SpeakerSegment(SpeakerSegmentBase):
    id: int
    transcription_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class DiarizationResult(BaseModel):
    segments: list[SpeakerSegment]
    total_segments: int
    speakers_count: int
    total_duration: float
