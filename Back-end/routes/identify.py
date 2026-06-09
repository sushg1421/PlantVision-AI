from fastapi import APIRouter, UploadFile, File, Form
from typing import List
from services.plantnet import identify_plant
from services.wikipedia import get_local_names
from services.gbif import get_gbif_data
from services.gbif import get_wikipedia_description
import tempfile, os, json

router = APIRouter()

# ── Lazy Gemini client ────────────────────────────────────────────────────────
_gemini_client = None

def get_gemini():
    global _gemini_client
    if _gemini_client is None:
        from google import genai
        _gemini_client = genai.Client(
            api_key=os.getenv("GEMINI_API_KEY")
        )
    return _gemini_client

# ── Translate plant info using Gemini ─────────────────────────────────────────
def translate_plant_info(scientific_name: str, description: str, language: str) -> str:
    if language == "English" or not description:
        return description

    prompt = f"""
Translate the following plant description into {language} language.
Plant: {scientific_name}
Description: {description}

Rules:
- Translate naturally into {language}
- Keep scientific names as-is
- Return ONLY the translated text, nothing else
"""
    try:
        client = get_gemini()
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text.strip()
    except Exception as e:
        print(f"Gemini translation failed: {e}")
        return description  # fallback to English


@router.post("/identify")
async def identify(
    images: List[UploadFile] = File(...),
    language: str = Form(default="English")
):
    print(f"DEBUG identify: language = '{language}'")
    temp_paths = []
    for img in images:
        suffix = os.path.splitext(img.filename)[1] or ".jpg"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
            f.write(await img.read())
            temp_paths.append(f.name)

    try:
        scientific_name, confidence  = identify_plant(temp_paths)
        family                       = get_gbif_data(scientific_name)
        wiki_title, description      = get_wikipedia_description(scientific_name)
        names                        = get_local_names(scientific_name, wiki_title)

        # Translate description if non-English selected
        if language and language != "English":
            description = translate_plant_info(scientific_name, description, language)

        return {
            "scientific_name": scientific_name,
            "confidence":      round(confidence * 100, 2),
            "family":          family,
            "description":     description,
            "local_names":     names,
        }
    finally:
        for path in temp_paths:
            os.unlink(path)