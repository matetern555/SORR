from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ...database import get_db
from ...models.transcription import Transcription
from ...models.speaker_segment import SpeakerSegment
from ...schemas.speaker_segment import SpeakerSegment as SpeakerSegmentSchema
from ...schemas.speaker_segment import DiarizationResult
from ...services.deepgram_diarization import transcribe_with_speaker_diarization

router = APIRouter()

@router.post("/analyze/{transcription_id}", response_model=DiarizationResult)
def analyze_speakers(
    transcription_id: int,
    db: Session = Depends(get_db)
):
    """
    Analizuje mówców w transkrypcji używając Deepgram API z prawdziwą diaryzacją mówców.
    """
    try:
        print(f"Rozpoczynanie analizy mówców dla transkrypcji ID: {transcription_id}")
        
        # Sprawdź czy transkrypcja istnieje
        transcription = db.query(Transcription).filter(Transcription.id == transcription_id).first()
        if not transcription:
            raise HTTPException(status_code=404, detail="Transkrypcja nie znaleziona")
        
        print(f"Znaleziono transkrypcję: {transcription.text[:50] if transcription.text else 'brak tekstu'}...")
        
        # Pobierz powiązany plik audio
        audio_file = transcription.audio_file
        if not audio_file:
            raise HTTPException(status_code=404, detail="Plik audio nie znaleziony")
        
        print(f"Plik audio istnieje: {audio_file.file_path}")
        
        # Normalizuj ścieżkę pliku (zamień backslashe na forward slashe)
        normalized_path = audio_file.file_path.replace("\\", "/")
        print(f"Znormalizowana ścieżka: {normalized_path}")
        
        # Otwórz plik audio i wykonaj transkrypcję z diaryzacją przez Deepgram
        with open(normalized_path, "rb") as audio_file_obj:
            print("Wykonywanie transkrypcji z diaryzacją mówców przez Deepgram...")
            transcription_result = transcribe_with_speaker_diarization(audio_file_obj, language="pl")
            
            # Pobierz segmenty mówców z wyniku
            speaker_segments = transcription_result.get("segments", [])
        
        print(f"Deepgram zwrócił {len(speaker_segments)} segmentów mówców")
        
        # Usuń stare segmenty jeśli istnieją
        db.query(SpeakerSegment).filter(
            SpeakerSegment.transcription_id == transcription_id
        ).delete()
        
        # Zapisz nowe segmenty w bazie danych
        db_segments = []
        for segment in speaker_segments:
            db_segment = SpeakerSegment(
                transcription_id=transcription_id,
                start_time=segment["start_time"],
                end_time=segment["end_time"],
                speaker_label=segment["speaker_label"],
                text=segment["text"],
                confidence=segment.get("confidence", 0.8)
            )
            db.add(db_segment)
            db_segments.append(db_segment)
        
        db.commit()
        
        # Odśwież segmenty, aby uzyskać ich ID
        for segment in db_segments:
            db.refresh(segment)
        
        print(f"Wyniki diaryzacji Deepgram zapisane do bazy danych, liczba segmentów: {len(db_segments)}")
        
        return DiarizationResult(
            segments=db_segments,
            total_segments=len(db_segments),
            speakers_count=len(set(seg.speaker_label for seg in db_segments)),
            total_duration=max(seg.end_time for seg in db_segments) if db_segments else 0.0
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Błąd podczas analizy mówców przez Deepgram: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Błąd podczas analizy mówców przez Deepgram: {str(e)}"
        )

@router.get("/segments/{transcription_id}", response_model=List[SpeakerSegmentSchema])
def get_speaker_segments(
    transcription_id: int,
    db: Session = Depends(get_db)
):
    """
    Pobiera segmenty mówców dla danej transkrypcji.
    """
    try:
        print(f"Pobieranie segmentów mówców dla transkrypcji ID: {transcription_id}")
        
        segments = db.query(SpeakerSegment).filter(
            SpeakerSegment.transcription_id == transcription_id
        ).order_by(SpeakerSegment.start_time).all()
        
        if not segments:
            raise HTTPException(
                status_code=404,
                detail="Nie znaleziono segmentów dla tej transkrypcji"
            )
        
        print(f"Znaleziono {len(segments)} segmentów")
        return segments
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Błąd podczas pobierania segmentów: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Błąd podczas pobierania segmentów: {str(e)}"
        )
