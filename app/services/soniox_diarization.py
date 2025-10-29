import os
from soniox.speech_service import SpeechClient, TranscriptionConfig
from soniox.transcribe_file import transcribe_bytes_stream
from typing import List, Dict, BinaryIO
from dotenv import load_dotenv

load_dotenv()

def get_soniox_client():
    """Tworzy i zwraca klienta Soniox"""
    api_key = os.getenv("SONIOX_API_KEY")
    if not api_key:
        raise ValueError("Brak klucza API Soniox. Sprawdź plik .env")
    
    return SpeechClient(api_key=api_key)

def transcribe_with_speaker_diarization(audio_file: BinaryIO, language: str = "pl") -> Dict:
    """
    Transkrybuje plik audio używając Soniox API z diaryzacją mówców.
    
    Args:
        audio_file: Plik audio do transkrypcji
        language: Kod języka (np. 'pl' dla polskiego)
    
    Returns:
        Dict: Wynik transkrypcji z diaryzacją mówców
    """
    try:
        client = get_soniox_client()
        
        print("Wykonywanie transkrypcji z diaryzacją mówców przez Soniox...")
        
        # Wczytaj cały plik audio
        audio_data = audio_file.read()
        print(f"Rozmiar pliku audio: {len(audio_data)} bajtów")
        
        # Użyj streaming API dla dużych plików
        # TODO: Musisz wybrać model w Soniox Console -> Project Settings -> Model selection
        # Przykładowe modele: 'en_us_general', 'en_us_phonecall', 'en_us_meeting', 'multilingual_v3'
        # Jeśli nie działa żaden model, dodaj środki na konto lub sprawdź ustawienia projektu
        result = transcribe_bytes_stream(
            audio=audio_data,
            client=client,
            model="",  # Musisz podać poprawny model - sprawdź w Soniox Console
            enable_global_speaker_diarization=True,
            max_num_speakers=2,  # Maksymalnie 2 mówców (konsultant + klient)
            chunk_size=131072  # 128KB chunks
        )
        
        # Przetwarzanie wyników
        segments = []
        for word in result.words:
            if hasattr(word, 'speaker') and word.speaker is not None:
                segments.append({
                    "start_time": word.start_time,
                    "end_time": word.end_time,
                    "speaker_label": f"SPEAKER_{word.speaker}",
                    "text": word.text,
                    "confidence": word.confidence if hasattr(word, 'confidence') else 0.8
                })
        
        # Grupowanie słów w zdania dla każdego mówcy
        speaker_segments = group_words_into_sentences(segments)
        
        return {
            "text": result.text,
            "language": language,
            "duration": result.duration if hasattr(result, 'duration') else 0.0,
            "segments": speaker_segments
        }
        
    except Exception as e:
        print(f"Szczegóły błędu Soniox: {str(e)}")
        raise Exception(f"Błąd podczas transkrypcji z diaryzacją przez Soniox: {str(e)}")

def group_words_into_sentences(word_segments: List[Dict]) -> List[Dict]:
    """
    Grupuje słowa w zdania dla każdego mówcy.
    
    Args:
        word_segments: Lista segmentów słów z informacją o mówcy
    
    Returns:
        List[Dict]: Lista segmentów zdań z informacją o mówcy
    """
    if not word_segments:
        return []
    
    sentence_segments = []
    current_speaker = None
    current_text = ""
    start_time = 0.0
    
    for segment in word_segments:
        speaker = segment["speaker_label"]
        text = segment["text"]
        start = segment["start_time"]
        end = segment["end_time"]
        
        # Jeśli zmienił się mówca lub to pierwsze słowo
        if current_speaker != speaker:
            # Zapisz poprzednie zdanie jeśli istnieje
            if current_text.strip():
                sentence_segments.append({
                    "start_time": start_time,
                    "end_time": sentence_segments[-1]["end_time"] if sentence_segments else end,
                    "speaker_label": current_speaker,
                    "text": current_text.strip(),
                    "confidence": 0.8
                })
            
            # Rozpocznij nowe zdanie
            current_speaker = speaker
            current_text = text
            start_time = start
        else:
            # Dodaj słowo do bieżącego zdania
            current_text += " " + text
    
    # Zapisz ostatnie zdanie
    if current_text.strip():
        sentence_segments.append({
            "start_time": start_time,
            "end_time": word_segments[-1]["end_time"],
            "speaker_label": current_speaker,
            "text": current_text.strip(),
            "confidence": 0.8
        })
    
    # Mapuj SPEAKER_0, SPEAKER_1 na KONSULTANT, KLIENT
    mapped_segments = []
    speaker_mapping = {}
    speaker_counter = 0
    
    for segment in sentence_segments:
        speaker = segment["speaker_label"]
        
        if speaker not in speaker_mapping:
            if speaker_counter == 0:
                speaker_mapping[speaker] = "KONSULTANT"
            else:
                speaker_mapping[speaker] = "KLIENT"
            speaker_counter += 1
        
        mapped_segment = segment.copy()
        mapped_segment["speaker_label"] = speaker_mapping[speaker]
        mapped_segments.append(mapped_segment)
    
    return mapped_segments
