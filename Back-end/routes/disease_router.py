# disease_router.py

import os
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import tensorflow as tf
import json, numpy as np
from fastapi import APIRouter, UploadFile, Form
from PIL import Image
import io

router = APIRouter(prefix="/disease", tags=["disease"])

# ── Lazy loading ──────────────────────────────────────────────────────────────
model = None
gemini_client = None

def get_model():
    global model
    if model is None:
        model_path = "models/disease_model.h5"
        if not os.path.exists(model_path):
            raise FileNotFoundError("Disease model not trained yet.")
        model = tf.keras.models.load_model(model_path)
    return model

def get_gemini():
    global gemini_client
    if gemini_client is None:
        from google import genai
        api_key = os.getenv("GEMINI_API_KEY")
        gemini_client = genai.Client(api_key=api_key)
    return gemini_client

with open("data/disease_cures.json") as f:
    CURES_DB = json.load(f)

with open("models/disease_classes.json") as f:
    CLASS_NAMES = json.load(f)

# ── Gemini: Generate cure info + dosage + translation ────────────────────────
def get_disease_info_from_gemini(disease_name: str, language: str) -> dict:
    prompt = f"""
You are an expert agricultural assistant for Indian farmers.

The disease detected is: {disease_name}

Provide the following information in {language} language in valid JSON format (no markdown, no backticks):
{{
  "display_name": "disease name in {language}",
  "symptoms": "2-3 line symptom description in {language}",
  "organic_cures": [
    "organic treatment 1 with simple instructions in {language}",
    "organic treatment 2 with simple instructions in {language}"
  ],
  "chemical_cures": [
    "ChemicalName1 - Xg per litre of water, spray every N days",
    "ChemicalName2 - Xg per litre of water, spray every N days"
  ],
  "prevention": "prevention tips in {language}",
  "severity": "Low or Medium or High (in English only)"
}}

Rules:
- Translate display_name, symptoms, organic_cures, prevention into {language}
- Keep chemical names in English but add dosage in {language}
- Severity must always be in English (Low / Medium / High)
- Use simple language for rural farmers with no formal education
- Respond ONLY with the JSON object, nothing else
"""
    try:
        client = get_gemini()
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())
    except Exception as e:
        print(f"Gemini generation failed: {e}")
        return {}  # triggers fallback

# ── Fallback: translate existing JSON data ────────────────────────────────────
def translate_disease_info(disease_name: str, cure_info: dict, language: str) -> dict:
    if language == "English":
        return cure_info

    prompt = f"""
You are a plant disease expert. Translate the following into {language}.

Disease: {disease_name}
Display Name: {cure_info.get('display_name', disease_name)}
Symptoms: {cure_info.get('symptoms', '')}
Organic Treatments: {', '.join(cure_info.get('organic_cures', []))}
Chemical Treatments: {', '.join(cure_info.get('chemical_cures', []))}
Prevention: {cure_info.get('prevention', '')}

Respond ONLY in valid JSON (no markdown, no backticks):
{{
  "display_name": "translated disease name",
  "symptoms": "translated symptoms",
  "organic_cures": ["translated cure 1", "translated cure 2"],
  "chemical_cures": ["chemical name 1", "chemical name 2"],
  "prevention": "translated prevention"
}}

Rules:
- Translate display_name, symptoms, organic_cures, prevention into {language}
- Keep chemical_cures as original English names
- Respond ONLY with JSON
"""
    try:
        client = get_gemini()
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        translated = json.loads(text.strip())
        translated["severity"] = cure_info.get("severity", "")
        return translated
    except Exception as e:
        print(f"Gemini translation failed: {e}")
        return cure_info

# ── Disease detection endpoint ────────────────────────────────────────────────
@router.post("/detect")
async def detect_disease(
    file: UploadFile,
    language: str = Form(default="English")
):
    print(f"DEBUG language = '{language}'")

    # 1. MobileNetV2 prediction
    m = get_model()
    img = Image.open(io.BytesIO(await file.read())).resize((224, 224))
    arr = np.expand_dims(np.array(img) / 255.0, 0)
    preds = m.predict(arr)[0]
    top_class = CLASS_NAMES[np.argmax(preds)]
    confidence = float(np.max(preds))

    # 2. Try Gemini first (generates cure + dosage + translation)
    cure_info = get_disease_info_from_gemini(top_class, language)

    # 3. Fallback to disease_cures.json if Gemini fails
    if not cure_info:
        print("Falling back to disease_cures.json")
        cure_info = CURES_DB.get(top_class, {})
        if language != "English":
            cure_info = translate_disease_info(top_class, cure_info, language)

    return {
        "disease": top_class,
        "confidence": confidence,
        "language": language,
        **cure_info
    }