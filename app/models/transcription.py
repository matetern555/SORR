from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..database import Base

class Transcription(Base):
    __tablename__ = "transcriptions"

    id = Column(Integer, primary_key=True, index=True)
    audio_file_id = Column(Integer, ForeignKey("audio_files.id"))
    text = Column(Text)
    language = Column(String)
    duration = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relacja z plikiem audio
    audio_file = relationship("AudioFile", back_populates="transcription")
    
    # Relacja z segmentami mówców
    speaker_segments = relationship("SpeakerSegment", back_populates="transcription", cascade="all, delete-orphan")

# Dodajemy relację do modelu AudioFile
from .audio import AudioFile
AudioFile.transcription = relationship("Transcription", back_populates="audio_file", uselist=False)




