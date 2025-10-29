from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class AudioFileBase(BaseModel):
    filename: str
    file_type: str
    duration: Optional[float] = None

class AudioFileCreate(AudioFileBase):
    pass

class AudioFile(AudioFileBase):
    id: int
    file_path: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True




