# Plik inicjalizacyjny pakietu schemas

from .audio import AudioFile, AudioFileCreate
from .transcription import Transcription, TranscriptionCreate
from .speaker_segment import SpeakerSegment, SpeakerSegmentCreate, DiarizationResult

__all__ = ["AudioFile", "AudioFileCreate", "Transcription", "TranscriptionCreate", "SpeakerSegment", "SpeakerSegmentCreate", "DiarizationResult"]
