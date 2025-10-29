import os
from deepgram import DeepgramClient
from typing import List, Dict, BinaryIO
from dotenv import load_dotenv
import io
import asyncio

try:
    load_dotenv()
except Exception as e:
    print(f"Ostrzeżenie: Nie można załadować pliku .env: {e}")

def get_deepgram_client():
    """Tworzy i zwraca klienta Deepgram"""
    # Z powodu problemów z .env używamy klucza bezpośrednio
    api_key = os.getenv("DEEPGRAM_API_KEY", "74988a83efa96261a8f892c93000cd227622373f")
    if not api_key:
        raise ValueError("Brak klucza API Deepgram. Sprawdź plik .env")
    
    # DeepgramClient przyjmuje api_key jako nazwany argument
    return DeepgramClient(api_key=api_key)

def transcribe_with_speaker_diarization_async(audio_file: BinaryIO, language: str = "pl") -> Dict:
    """
    Transkrybuje plik audio używając Deepgram API z diaryzacją mówców (wersja async).
    
    Args:
        audio_file: Plik audio do transkrypcji
        language: Kod języka (np. 'pl' dla polskiego, 'en' dla angielskiego)
    
    Returns:
        Dict: Wynik transkrypcji z diaryzacją mówców
    """
    try:
        deepgram = get_deepgram_client()
        
        print("Wykonywanie transkrypcji z diaryzacją mówców przez Deepgram...")
        
        # Wczytaj cały plik audio
        audio_data = audio_file.read()
        print(f"Rozmiar pliku audio: {len(audio_data)} bajtów")
        
        # Mapowanie języka - Deepgram używa innych kodów
        language_map = {
            "pl": "pl",  # Polski
            "en": "en",  # Angielski
        }
        deepgram_language = language_map.get(language, "en")
        
        print("Wysyłanie żądania do Deepgram...")
        # Deepgram v5 - NIE podajemy encoding, pozwalamy API wykryć format automatycznie
        # Deepgram automatycznie wykrywa format audio na podstawie danych
        response = deepgram.listen.v1.media.transcribe_file(
            request=audio_data,
            model="nova-2",
            language=deepgram_language,
            punctuate=True,
            smart_format=True,
            diarize=True  # Włącz diaryzację mówców
        )
        
        print("Otrzymano odpowiedź z Deepgram")
        
        # Debug: Sprawdź strukturę odpowiedzi
        print(f"Typ odpowiedzi: {type(response)}")
        print(f"Ma results: {hasattr(response, 'results')}")
        
        if not hasattr(response, 'results') or not response.results:
            print("Ostrzeżenie: Brak wyników w odpowiedzi Deepgram")
            return {
                "text": "",
                "language": language,
                "duration": 0.0,
                "segments": []
            }
        
        if not response.results.channels or len(response.results.channels) == 0:
            print("Ostrzeżenie: Brak kanałów w odpowiedzi Deepgram")
            print(f"Liczba kanałów: {len(response.results.channels) if response.results.channels else 0}")
            print(f"Struktura response.results: {dir(response.results)}")
            return {
                "text": "",
                "language": language,
                "duration": 0.0,
                "segments": []
            }
        
        # Przetwarzanie wyników
        transcript = response.results.channels[0].alternatives[0].transcript
        print(f"Transkrypcja: {transcript[:100]}...")
        
        # Pobierz segmenty z diaryzacją
        diarization_results = response.results.channels[0].alternatives[0].words
        print(f"Liczba słów z diaryzacją: {len(diarization_results) if diarization_results else 0}")
        
        # Grupuj słowa w segmenty dla każdego mówcy
        speaker_segments = group_words_into_sentences(diarization_results)
        
        # Mapuj SPEAKER_0, SPEAKER_1 na KONSULTANT, KLIENT
        mapped_segments = map_speakers(speaker_segments)
        
        return {
            "text": transcript,
            "language": language,
            "duration": response.metadata.duration if hasattr(response, 'metadata') else 0.0,
            "segments": mapped_segments
        }
        
    except Exception as e:
        print(f"Szczegóły błędu Deepgram: {str(e)}")
        import traceback
        traceback.print_exc()
        raise Exception(f"Błąd podczas transkrypcji z diaryzacją przez Deepgram: {str(e)}")

def transcribe_with_speaker_diarization(audio_file: BinaryIO, language: str = "pl") -> Dict:
    """
    Transkrypcja z diaryzacją mówców - synchroniczna funkcja.
    """
    return transcribe_with_speaker_diarization_async(audio_file, language)

def group_words_into_sentences(words: List) -> List[Dict]:
    """
    Grupuje słowa w zdania dla każdego mówcy.
    
    Args:
        words: Lista słów z informacją o mówcy (format Deepgram)
    
    Returns:
        List[Dict]: Lista segmentów zdań z informacją o mówcy
    """
    if not words:
        return []
    
    # Debug: Sprawdź typ pierwszego słowa
    if len(words) > 0:
        print(f"Typ pierwszego słowa: {type(words[0])}")
        print(f"Czy jest dict: {isinstance(words[0], dict)}")
        print(f"Ma atrybut speaker: {hasattr(words[0], 'speaker')}")
        if hasattr(words[0], 'speaker'):
            print(f"Speaker: {words[0].speaker}")
        if hasattr(words[0], 'word'):
            print(f"Word: {words[0].word}")
    
    sentence_segments = []
    current_speaker = None
    current_text = ""
    start_time = 0.0
    
    for word in words:
        # Deepgram v5 zwraca słowa jako obiekty z atrybutami
        if hasattr(word, 'speaker'):
            speaker = word.speaker
            text = word.word if hasattr(word, 'word') else ''
            start = word.start if hasattr(word, 'start') else 0.0
            end = word.end if hasattr(word, 'end') else 0.0
        elif isinstance(word, dict):
            speaker = word.get('speaker', None)
            text = word.get('word', '')
            start = word.get('start', 0.0)
            end = word.get('end', 0.0)
        else:
            # Pomiń jeśli nie ma informacji o mówcy
            continue
        
        # Jeśli zmienił się mówca lub to pierwsze słowo
        if current_speaker != speaker:
            # Zapisz poprzednie zdanie jeśli istnieje
            if current_text.strip():
                sentence_segments.append({
                    "start_time": start_time,
                    "end_time": sentence_segments[-1]["end_time"] if sentence_segments else end,
                    "speaker_label": f"SPEAKER_{current_speaker}",
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
        last_word = words[-1]
        last_end = last_word.get('end', 0.0) if isinstance(last_word, dict) else 0.0
        sentence_segments.append({
            "start_time": start_time,
            "end_time": last_end,
            "speaker_label": f"SPEAKER_{current_speaker}",
            "text": current_text.strip(),
            "confidence": 0.8
        })
    
    return sentence_segments

def map_speakers(segments: List[Dict]) -> List[Dict]:
    """
    Mapuje SPEAKER_0, SPEAKER_1 na KONSULTANT, KLIENT.
    
    Args:
        segments: Lista segmentów z SPEAKER_0, SPEAKER_1
    
    Returns:
        List[Dict]: Lista segmentów z KONSULTANT, KLIENT
    """
    mapped_segments = []
    speaker_mapping = {}
    speaker_counter = 0
    
    for segment in segments:
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

