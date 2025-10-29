import os
import json
from openai import OpenAI
from typing import Dict, List
from datetime import timedelta
from dotenv import load_dotenv

try:
    load_dotenv()
except Exception as e:
    print(f"Ostrzeżenie: Nie można załadować pliku .env: {e}")

def get_openai_client():
    """Tworzy i zwraca klienta OpenAI"""
    # TODO: Usunąć hardkod po naprawie pliku .env
    api_key = os.getenv("OPENAI_API_KEY") or "sk-proj-..."
    
    if not api_key or api_key == "sk-proj-...":
        raise ValueError("Brak klucza API OpenAI. Sprawdź plik .env lub dodaj klucz bezpośrednio w kodzie")
    
    return OpenAI(api_key=api_key)

# Globalny System Prompt zgodnie ze specyfikacją
GLOBAL_SYSTEM_PROMPT = """Analizuj rozmowy konsultant–klient pod kątem jakości komunikacji: jasność przekazu, empatia, logika diagnozy i skuteczność pomocy. Nie oceniaj zgodności z procedurami. Każdą kategorię oceń w skali 1–5, gdzie 1 = bardzo słabo, 3 = poprawnie, 5 = wzorowo. Dla każdej kategorii podaj krótki komentarz i 1–2 cytaty (z czasem). Na końcu opisz emocje klienta i konsultanta: nastroje na początku/końcu oraz krótki opis trendu."""

# Kategorie dla SERVICE zgodnie ze specyfikacją
SERVICE_CATEGORIES = [
    {
        "name": "Powitanie i ton",
        "weight": 10,
        "prompt": "Oceń pierwsze wrażenie i ton.",
        "points_1": "Brak powitania/zimno",
        "points_3": "Formalnie",
        "points_5": "Ciepło, naturalnie"
    },
    {
        "name": "Identyfikacja problemu",
        "weight": 20,
        "prompt": "Sprawdź, czy konsultant naprawdę zrozumiał zgłoszenie (trafne pytania, potwierdzenie).",
        "points_1": "Nie pyta",
        "points_3": "Częściowe dopytanie",
        "points_5": "Trafne pytania + parafraza"
    },
    {
        "name": "Rozwiązanie sprawy",
        "weight": 25,
        "prompt": "Oceń skuteczność i jasność pomocy (kroki, upewnienie efektu).",
        "points_1": "Brak pomocy",
        "points_3": "Częściowo",
        "points_5": "Pełne rozwiązanie i upewnienie („Działa?”)"
    },
    {
        "name": "Jasność komunikacji",
        "weight": 15,
        "prompt": "Oceń prosty język, tempo, prowadzenie krok po kroku.",
        "points_1": "Żargon",
        "points_3": "Poprawnie",
        "points_5": "Prosto i cierpliwie"
    },
    {
        "name": "Finalizacja rozmowy",
        "weight": 15,
        "prompt": "Oceń domknięcie i pozytywne zakończenie.",
        "points_1": "Nagle",
        "points_3": "Formalnie",
        "points_5": "Podsumowanie + propozycja dalszej pomocy"
    },
    {
        "name": "Soft-skills",
        "weight": 15,
        "prompt": "Oceń empatię, cierpliwość, reagowanie na emocje.",
        "points_1": "Chłodno/poirytowanie",
        "points_3": "Neutralnie",
        "points_5": "Spokojnie i empatycznie"
    }
]

def format_timestamp(seconds: float) -> str:
    """Formatuje sekundy na format HH:MM:SS"""
    td = timedelta(seconds=int(seconds))
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def prepare_transcription_for_evaluation(speaker_segments: List[Dict]) -> str:
    """
    Przygotowuje transkrypcję w formacie dla GPT-4.
    
    Args:
        speaker_segments: Lista segmentów mówców z bazy danych
    
    Returns:
        str: Sformatowana transkrypcja
    """
    formatted_lines = []
    
    for segment in speaker_segments:
        speaker = segment.speaker_label
        text = segment.text or ""
        start_time = format_timestamp(segment.start_time)
        
        formatted_lines.append(f"{start_time} – {speaker}: \"{text}\"")
    
    return "\n".join(formatted_lines)

def evaluate_conversation_gpt4(transcription_text: str, speaker_segments: List[Dict]) -> Dict:
    """
    Ocenia rozmowę używając GPT-4.
    
    Args:
        transcription_text: Pełny tekst transkrypcji
        speaker_segments: Lista segmentów mówców
    
    Returns:
        Dict: Wynik oceny z kategoriami, sentymentem i komentarzem
    """
    client = get_openai_client()
    
    # Przygotuj transkrypcję w formacie z timestampami
    formatted_transcription = prepare_transcription_for_evaluation(speaker_segments)
    
    # Buduj prompt z kategoriami
    categories_prompt = "\n\nOceń rozmowę w następujących kategoriach:\n\n"
    for i, cat in enumerate(SERVICE_CATEGORIES, 1):
        categories_prompt += f"{i}. {cat['name']} ({cat['weight']}%)\n"
        categories_prompt += f"   Cel: {cat['prompt']}\n"
        categories_prompt += f"   Skala: 1={cat['points_1']}, 3={cat['points_3']}, 5={cat['points_5']}\n\n"
    
    # Prompt dla GPT-4
    user_prompt = """Przeanalizuj poniższą rozmowę telefoniczną z obsługi klienta.

TRANSCRIPTION:
""" + formatted_transcription + """

""" + categories_prompt + """

Wymagania:
- Dla każdej kategorii podaj ocenę (1-5), krótki komentarz i 1-2 cytaty z czasem
- Na końcu napisz krótki komentarz końcowy (2-4 zdania)

Zwróć odpowiedź w formacie JSON:
{
  "categories": [
    {
      "name": "nazwa kategorii",
      "score": 1-5,
      "comment": "komentarz",
      "quotes": [
        {"speaker": "KONSULTANT lub KLIENT", "timestamp": "HH:MM:SS", "text": "cytat", "is_positive": true/false}
      ]
    }
  ],
  "final_comment": "komentarz końcowy"
}"""
    
    print("Wysyłanie żądania do GPT-4...")
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": GLOBAL_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3
        )
        
        content = response.choices[0].message.content
        
        # Wyciągnij JSON z odpowiedzi (może zawierać markdown)
        if "```json" in content:
            json_start = content.find("```json") + 7
            json_end = content.find("```", json_start)
            content = content[json_start:json_end].strip()
        elif "```" in content:
            json_start = content.find("```") + 3
            json_end = content.find("```", json_start)
            content = content[json_start:json_end].strip()
        
        result = json.loads(content)
        print("GPT-4 odpowiedział pomyślnie")
        
        return result
        
    except Exception as e:
        print(f"Błąd GPT-4: {str(e)}")
        raise Exception(f"Błąd podczas oceny przez GPT-4: {str(e)}")

def calculate_overall_score(category_results: List[Dict]) -> float:
    """
    Oblicza wynik końcowy na podstawie kategorii i wag.
    
    Args:
        category_results: Lista wyników kategorii z score i weight
    
    Returns:
        float: Wynik końcowy 0-100
    """
    total_points = 0.0
    
    for cat_result in category_results:
        score = cat_result.get("score", 3)
        weight = cat_result.get("weight", 0)
        
        # Punkty = (score / 5) * weight
        points = (score / 5.0) * weight
        total_points += points
    
    return round(total_points, 2)

def calculate_grade(score: float) -> str:
    """
    Oblicza ocenę literową na podstawie wyniku.
    
    Args:
        score: Wynik 0-100
    
    Returns:
        str: Ocena A, B, C lub D
    """
    if score >= 85:
        return "A"
    elif score >= 75:
        return "B"
    elif score >= 60:
        return "C"
    else:
        return "D"

def evaluate_conversation(transcription_text: str, speaker_segments: List[Dict]) -> Dict:
    """
    Główna funkcja oceny rozmowy.
    
    Args:
        transcription_text: Pełny tekst transkrypcji
        speaker_segments: Lista segmentów mówców z bazy danych
    
    Returns:
        Dict: Kompletny wynik oceny
    """
    # Wywołaj GPT-4
    gpt_result = evaluate_conversation_gpt4(transcription_text, speaker_segments)
    
    # Połącz wyniki GPT z wagami kategorii
    category_results = []
    for i, cat_result in enumerate(gpt_result.get("categories", [])):
        category_results.append({
            "name": cat_result.get("name", SERVICE_CATEGORIES[i]["name"]),
            "weight": SERVICE_CATEGORIES[i]["weight"],
            "score": cat_result.get("score", 3),
            "comment": cat_result.get("comment", ""),
            "quotes": cat_result.get("quotes", [])
        })
    
    # Oblicz wynik końcowy
    overall_score = calculate_overall_score(category_results)
    grade = calculate_grade(overall_score)
    
    return {
        "category_results": category_results,
        "final_comment": gpt_result.get("final_comment", ""),
        "overall_score": overall_score,
        "grade": grade
    }

