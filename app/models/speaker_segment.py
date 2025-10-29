from sqlalchemy import Column, Integer, String, Float, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base

class SpeakerSegment(Base):
    __tablename__ = "speaker_segments"
    
    id = Column(Integer, primary_key=True, index=True)
    transcription_id = Column(Integer, ForeignKey("transcriptions.id"), nullable=False)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    speaker_label = Column(String(50), nullable=False)
    text = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relacja z transkrypcją
    transcription = relationship("Transcription", back_populates="speaker_segments")
