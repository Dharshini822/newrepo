import re
from deep_translator import GoogleTranslator

# Verified Indian Sign Language (ISL) Gloss -> Tamil & English Dictionary
ISL_GLOSSARY = {
    # Greetings & Courtesies
    "HELLO": {"ta": "வணக்கம்", "en": "Hello", "pronunciation": "Vanakkam"},
    "HI": {"ta": "வணக்கம்", "en": "Hi", "pronunciation": "Vanakkam"},
    "THANK YOU": {"ta": "நன்றி", "en": "Thank you", "pronunciation": "Nandri"},
    "THANKS": {"ta": "நன்றி", "en": "Thanks", "pronunciation": "Nandri"},
    "WELCOME": {"ta": "நல்வரவு", "en": "Welcome", "pronunciation": "Nalvaravu"},
    "PLEASE": {"ta": "தயவுசெய்து", "en": "Please", "pronunciation": "Thayavuseidhu"},
    "SORRY": {"ta": "மன்னிக்கவும்", "en": "Sorry", "pronunciation": "Mannikkavum"},
    "GOOD MORNING": {"ta": "காலை வணக்கம்", "en": "Good morning", "pronunciation": "Kaalai vanakkam"},
    "GOOD NIGHT": {"ta": "இனிய இரவு", "en": "Good night", "pronunciation": "Iniya iravu"},
    
    # Common Responses & Status
    "YES": {"ta": "ஆம்", "en": "Yes", "pronunciation": "Aam"},
    "NO": {"ta": "இல்லை", "en": "No", "pronunciation": "Illai"},
    "OK": {"ta": "சரி", "en": "OK", "pronunciation": "Sari"},
    "GOOD": {"ta": "நல்லது", "en": "Good", "pronunciation": "Nalladhu"},
    "BAD": {"ta": "மோசமானது", "en": "Bad", "pronunciation": "Mosamaanadhu"},
    "HELP": {"ta": "உதவி", "en": "Help", "pronunciation": "Udhavi"},
    "STOP": {"ta": "நிறுத்து", "en": "Stop", "pronunciation": "Nirutthu"},
    "WAIT": {"ta": "காத்திருங்கள்", "en": "Wait", "pronunciation": "Kaatthirungal"},
    
    # Essentials & Family
    "WATER": {"ta": "தண்ணீர்", "en": "Water", "pronunciation": "Thanneer"},
    "FOOD": {"ta": "உணவு", "en": "Food", "pronunciation": "Unavu"},
    "FRIEND": {"ta": "நண்பர்", "en": "Friend", "pronunciation": "Nanbar"},
    "FAMILY": {"ta": "குடும்பம்", "en": "Family", "pronunciation": "Kudumbam"},
    "HOME": {"ta": "வீடு", "en": "Home", "pronunciation": "Veedu"},
    "SCHOOL": {"ta": "பள்ளி", "en": "School", "pronunciation": "Palli"},
    "LOVE": {"ta": "அன்பு", "en": "Love", "pronunciation": "Anbu"},
    "I LOVE YOU": {"ta": "நான் உன்னை நேசிக்கிறேன்", "en": "I love you", "pronunciation": "Naan unnai nesikkiren"},
    
    # Common Questions & Pronouns
    "WHAT": {"ta": "என்ன", "en": "What", "pronunciation": "Enna"},
    "WHERE": {"ta": "எங்கே", "en": "Where", "pronunciation": "Engae"},
    "WHEN": {"ta": "எப்போது", "en": "When", "pronunciation": "Eppodhu"},
    "HOW": {"ta": "எப்படி", "en": "How", "pronunciation": "Eppadi"},
    "WHO": {"ta": "யார்", "en": "Who", "pronunciation": "Yaar"},
    "I": {"ta": "நான்", "en": "I", "pronunciation": "Naan"},
    "YOU": {"ta": "நீங்கள்", "en": "You", "pronunciation": "Neengal"},
    "WE": {"ta": "நாம்", "en": "We", "pronunciation": "Naam"}
}

# Single alphabet mapping for ISL finger spelling
for char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
    if char not in ISL_GLOSSARY:
        ISL_GLOSSARY[char] = {
            "ta": f"எழுத்து {char}",
            "en": f"Letter {char}",
            "pronunciation": f"Eluthu {char}"
        }

def translate_text(text: str, target_lang: str = "ta", source_lang: str = "auto") -> dict:
    """
    Translates input text to target language ('ta' for Tamil, 'en' for English).
    Uses verified ISL dictionary first for accurate sign semantics, with deep-translator fallback.
    """
    if not text or not text.strip():
        return {
            "original": "",
            "translated": "",
            "target_lang": target_lang,
            "provider": "none",
            "pronunciation": ""
        }

    clean_text = text.strip()
    upper_key = clean_text.upper()

    # 1. Check verified glossary
    if target_lang == "ta" and upper_key in ISL_GLOSSARY:
        entry = ISL_GLOSSARY[upper_key]
        return {
            "original": clean_text,
            "translated": entry["ta"],
            "target_lang": "ta",
            "provider": "isl_verified_dictionary",
            "pronunciation": entry.get("pronunciation", "")
        }
    elif target_lang == "en" and upper_key in ISL_GLOSSARY:
        entry = ISL_GLOSSARY[upper_key]
        return {
            "original": clean_text,
            "translated": entry["en"],
            "target_lang": "en",
            "provider": "isl_verified_dictionary",
            "pronunciation": ""
        }

    # 2. Online deep-translator fallback
    try:
        translated_result = GoogleTranslator(source=source_lang, target=target_lang).translate(clean_text)
        return {
            "original": clean_text,
            "translated": translated_result,
            "target_lang": target_lang,
            "provider": "google_translator",
            "pronunciation": ""
        }
    except Exception as e:
        print(f"[TranslationService] Online translation error: {e}")
        # If offline and in glossary, return glossary value
        if upper_key in ISL_GLOSSARY:
            return {
                "original": clean_text,
                "translated": ISL_GLOSSARY[upper_key].get(target_lang, clean_text),
                "target_lang": target_lang,
                "provider": "isl_fallback_dictionary",
                "pronunciation": ISL_GLOSSARY[upper_key].get("pronunciation", "")
            }
        return {
            "original": clean_text,
            "translated": clean_text,
            "target_lang": target_lang,
            "provider": "untranslated",
            "error": "Translation service unreachable and term not in offline dictionary."
        }

def get_glossary_list():
    """Returns the full list of verified signs in the ISL glossary."""
    items = []
    for key, val in ISL_GLOSSARY.items():
        if len(key) > 1:  # Filter word signs first
            items.append({
                "sign": key,
                "english": val["en"],
                "tamil": val["ta"],
                "pronunciation": val.get("pronunciation", "")
            })
    return sorted(items, key=lambda x: x["sign"])
