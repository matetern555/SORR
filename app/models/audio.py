from sqlalchemy import Column, Integer, String, DateTime, Float
from sqlalchemy.sql import func
from ..database import Base

class AudioFile(Base):
    __tablename__ = "audio_files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, unique=True, index=True)
    file_path = Column(String)
    duration = Column(Float)
    file_type = Column(String)  # MP3 lub WAV
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())




