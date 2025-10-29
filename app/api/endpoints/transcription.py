from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import os

from ...database import get_db
from ...models.audio import AudioFile
from ...models.transcription import Transcription
from ...schemas.transcription import Transcription as TranscriptionSchema
from ...services.transcription import get_openai_client, transcribe_audio

router = APIRouter()

@router.get("/test-api/")
def test_openai_api():
    """Endpoint testowy do sprawdzenia połączenia z OpenAI"""
    try:
        client = get_openai_client()
        # Sprawdzamy tylko czy klucz API jest poprawny
        return {"status": "OK", "message": "Połączenie z OpenAI działa prawidłowo"}
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Błąd połączenia z OpenAI: {str(e)}"
        )

@router.post("/transcribe/{audio_id}", response_model=TranscriptionSchema)
def create_transcription(
    audio_id: int,
    db: Session = Depends(get_db)
):
    # Sprawdź czy plik audio istnieje
    audio_file = db.query(AudioFile).filter(AudioFile.id == audio_id).first()
    if not audio_file:
        raise HTTPException(status_code=404, detail="Plik audio nie znaleziony")
    
    # Sprawdź czy transkrypcja już istnieje
    existing_transcription = db.query(Transcription).filter(
        Transcription.audio_file_id == audio_id
    ).first()
    
    if existing_transcription:
        raise HTTPException(
            status_code=400,
            detail="Transkrypcja dla tego pliku już istnieje"
        )
    
    try:
        # Otwórz plik audio
        with open(audio_file.file_path, "rb") as audio:
            # Wykonaj transkrypcję
            result = transcribe_audio(audio)
        
        # Zapisz transkrypcję w bazie danych
        transcription = Transcription(
            audio_file_id=audio_id,
            text=result["text"],
            language=result["language"],
            duration=result["duration"]
        )
        
        db.add(transcription)
        db.commit()
        db.refresh(transcription)
        
        return transcription
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Błąd podczas transkrypcji: {str(e)}"
        )

@router.get("/transcriptions/", response_model=List[TranscriptionSchema])
def list_transcriptions(db: Session = Depends(get_db)):
    return db.query(Transcription).all()

@router.get("/transcriptions/{transcription_id}", response_model=TranscriptionSchema)
def get_transcription(transcription_id: int, db: Session = Depends(get_db)):
    transcription = db.query(Transcription).filter(
        Transcription.id == transcription_id
    ).first()
    
    if transcription is None:
        raise HTTPException(
            status_code=404,
            detail="Transkrypcja nie znaleziona"
        )
    
    return transcription