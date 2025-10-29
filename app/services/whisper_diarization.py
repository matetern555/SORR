from typing import List, Dict
import re

def create_speaker_segments_from_text(text: str, duration: float = 0.0) -> List[Dict]:
    """
    Tworzy segmenty mówców na podstawie istniejącej transkrypcji tekstowej.
    Dzieli tekst na zdania i rotuje mówców.
    
    Args:
        text: Tekst transkrypcji
        duration: Całkowity czas trwania audio (w sekundach)
    
    Returns:
        List[Dict]: Lista segmentów z informacją o mówcy
    """
    try:
        print(f"Tworzenie segmentów mówców z tekstu (długość: {len(text)} znaków, czas: {duration}s)")
        
        # Podziel tekst na zdania
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            # Jeśli nie ma zdań, zwróć cały tekst jako jeden segment
            return [{
                "start_time": 0.0,
                "end_time": duration,
                "speaker_label": "KONSULTANT",
                "text": text.strip(),
                "confidence": 0.8
            }]
        
        segments = []
        speaker_rotation = ["KONSULTANT", "KLIENT"]
        speaker_idx = 0
        
        # Oblicz czas na zdanie
        time_per_sentence = duration / len(sentences) if duration > 0 else 5.0
        
        current_time = 0.0
        for sentence in sentences:
            # Oblicz czas trwania zdania na podstawie długości
            sentence_duration = max(2.0, len(sentence) / 20.0)  # ~20 znaków na sekundę
            
            # Jeśli mamy całkowity czas, użyj go
            if duration > 0:
                sentence_duration = time_per_sentence
            
            segments.append({
                "start_time": round(current_time, 2),
                "end_time": round(current_time + sentence_duration, 2),
                "speaker_label": speaker_rotation[speaker_idx % 2],
                "text": sentence.strip(),
                "confidence": 0.8
            })
            
            current_time += sentence_duration
            speaker_idx += 1
        
        print(f"Utworzono {len(segments)} segmentów mówców")
        return segments
        
    except Exception as e:
        print(f"Błąd podczas tworzenia segmentów mówców: {str(e)}")
        raise Exception(f"Nie udało się utworzyć segmentów mówców: {str(e)}")
