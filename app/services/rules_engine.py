"""
Rules Engine - Weryfikacja fraz i zastosowanie reguł
"""
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import timedelta

def find_phrases_in_transcription(transcription_text: str, speaker_segments: List[Dict], 
                                   phrases: List[str], case_sensitive: bool = False) -> List[Dict]:
    """
    Wyszukuje frazy w transkrypcji i zwraca dopasowania z timestampami.
    
    Args:
        transcription_text: Pełny tekst transkrypcji
        speaker_segments: Lista segmentów mówców
        phrases: Lista fraz do wyszukania
        case_sensitive: Czy wyszukiwanie jest wrażliwe na wielkość liter
    
    Returns:
        Lista dopasowań: [{"phrase": "...", "found": True/False, "timestamp": "...", "speaker": "..."}]
    """
    matches = []
    
    for phrase in phrases:
        found = False
        timestamp = None
        speaker = None
        
        # Wyszukaj frazę w transkrypcji
        if case_sensitive:
            pattern = re.escape(phrase)
        else:
            pattern = re.escape(phrase.lower())
            transcription_lower = transcription_text.lower()
        
        search_text = transcription_text if case_sensitive else transcription_lower
        
        if re.search(pattern, search_text):
            found = True
            
            # Znajdź timestamp i mówcę dla pierwszej frazy
            for segment in speaker_segments:
                segment_text = segment.get("text", "") or ""
                search_segment = segment_text if case_sensitive else segment_text.lower()
                
                if re.search(pattern, search_segment):
                    timestamp = format_timestamp(segment.get("start_time", 0))
                    speaker = segment.get("speaker_label", "")
                    break
        
        matches.append({
            "phrase": phrase,
            "found": found,
            "timestamp": timestamp,
            "speaker": speaker
        })
    
    return matches

def format_timestamp(seconds: float) -> str:
    """Formatuje sekundy na format HH:MM:SS"""
    td = timedelta(seconds=int(seconds))
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def apply_required_phrases_penalty(base_score: float, phrase_matches: List[Dict]) -> Tuple[float, List[str]]:
    """
    Zastosowuje kary za brak fraz obowiązkowych.
    
    Args:
        base_score: Wynik bazowy
        phrase_matches: Lista dopasowań fraz
    
    Returns:
        Tuple: (nowy wynik, lista opisów zastosowanych kar)
    """
    adjustments = []
    penalty = 0.0
    
    for match in phrase_matches:
        if not match["found"]:
            # Domyślna kara -1 punkt za brak frazy obowiązkowej
            penalty += 1.0
            adjustments.append(f"Brak frazy obowiązkowej: '{match['phrase']}' (-1 pkt)")
    
    return base_score - penalty, adjustments

def apply_forbidden_phrases_penalty(base_score: float, phrase_matches: List[Dict]) -> Tuple[float, Optional[float], List[str]]:
    """
    Zastosowuje kary za użycie fraz zakazanych.
    
    Args:
        base_score: Wynik bazowy
        phrase_matches: Lista dopasowań fraz
    
    Returns:
        Tuple: (nowy wynik, hard_fail_threshold, lista opisów zastosowanych kar)
    """
    adjustments = []
    penalty = 0.0
    hard_fail_threshold = None
    
    for match in phrase_matches:
        if match["found"]:
            # Domyślna kara -3 punkty za użycie frazy zakazanej
            penalty += 3.0
            adjustments.append(f"Użyto frazy zakazanej: '{match['phrase']}' (-3 pkt)")
            
            # Jeśli fraza jest krytyczna, zastosuj hard-fail (sufit 60%)
            hard_fail_threshold = 60.0
    
    return base_score - penalty, hard_fail_threshold, adjustments

def apply_rules(base_score: float, transcription_text: str, speaker_segments: List[Dict], 
                rules: List[Dict]) -> Tuple[float, List[Dict]]:
    """
    Uproszczone reguły - tylko podstawowe funkcje.
    
    Args:
        base_score: Wynik bazowy
        transcription_text: Pełny tekst transkrypcji
        speaker_segments: Lista segmentów mówców
        rules: Lista reguł (pomijane w tej wersji)
    
    Returns:
        Tuple: (wynik bez zmian, pusta lista reguł)
    """
    # Na razie pomijamy skomplikowane reguły IF-THEN
    # Zostają tylko frazy obowiązkowe/zakazane i hard-fail
    return base_score, []

def apply_hard_fail_threshold(score: float, threshold: Optional[float]) -> float:
    """
    Zastosowuje hard-fail (sufit wyniku).
    
    Args:
        score: Aktualny wynik
        threshold: Sufit wyniku (np. 60%)
    
    Returns:
        Wynik po zastosowaniu sufitowania
    """
    if threshold is not None and score > threshold:
        return threshold
    return score

def get_default_service_scorecard() -> Dict[str, Any]:
    """
    Zwraca domyślną konfigurację karty SERVICE z frazami.
    """
    return {
        "name": "SERVICE_DEFAULT",
        "scorecard_type": "SERVICE",
        "required_phrases": [
            "Czy mogę w czymś jeszcze pomóc?",
            "Dzień dobry"
        ],
        "forbidden_phrases": [
            "To nie mój problem",
            "Nie wiem"
        ],
        "rules": []  # Uproszczone - bez skomplikowanych reguł
    }

