import os
from openai import OpenAI
from typing import BinaryIO, Dict
from dotenv import load_dotenv

try:
    load_dotenv()
except Exception as e:
    print(f"Ostrzeżenie: Nie można załadować pliku .env: {e}")

def get_openai_client():
    """Tworzy i zwraca klienta OpenAI"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Brak klucza API OpenAI. Sprawdź plik .env")
    
    # Inicjalizacja klienta bez dodatkowych parametrów
    return OpenAI(
        api_key=api_key,
    )

def transcribe_audio(audio_file: BinaryIO, language: str = "pl") -> Dict:
    """
    Transkrybuje plik audio używając OpenAI Whisper API.
    """
    try:
        client = get_openai_client()
        response = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language=language
        )
        
        return {
            "text": response.text,
            "language": language,
            "duration": 0.0
        }
    except Exception as e:
        print(f"Szczegóły błędu: {str(e)}")
        raise Exception(f"Błąd podczas transkrypcji: {str(e)}")