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

# ── Lazy loading — nothing runs at startup ────────────────────────────────────
model = None
gemini_client = None

def get_model():
    global model
    if model is None:
        model_path = "models/disease_model.h5"
        if not os.path.exists(model_path):
            raise FileNotFoundError("Disease model not trained yet. Run ml/train.py first.")
        model = tf.keras.models.load_model(model_path)
    return model

def get_gemini():
    global gemini_client
    if gemini_client is None:
        from google import genai
        api_key = os.getenv("GEMINI_API_KEY", "AIzaSyBm3IOObR5Y4tziSXw_dp1ZftSjVVldRA8")
        gemini_client = genai.Client(api_key=api_key)
    return gemini_client

with open("data/disease_cures.json") as f:
    CURES_DB = json.load(f)

with open("models/disease_classes.json") as f:
    CLASS_NAMES = json.load(f)

# ── Translate using Gemini ────────────────────────────────────────────────────
def translate_disease_info(disease_name: str, cure_info: dict, language: str) -> dict:
    if language == "English":
        return cure_info

    prompt = f"""
You are a plant disease expert. Translate the following plant disease information into {language} language.

Disease: {disease_name}
Display Name: {cure_info.get('display_name', disease_name)}
Symptoms: {cure_info.get('symptoms', '')}
Organic Treatments: {', '.join(cure_info.get('organic_cures', []))}
Chemical Treatments: {', '.join(cure_info.get('chemical_cures', []))}
Prevention: {cure_info.get('prevention', '')}

Respond ONLY in valid JSON format (no markdown, no backticks) with these exact keys:
{{
  "display_name": "translated disease name in {language}",
  "symptoms": "translated symptoms in {language}",
  "organic_cures": ["translated cure 1", "translated cure 2"],
  "chemical_cures": ["chemical name 1", "chemical name 2"],
  "prevention": "translated prevention tips in {language}"
}}

Rules:
- Translate display_name, symptoms, organic_cures, prevention into {language}
- Keep chemical_cures as original chemical names (do not translate)
- Respond ONLY with the JSON object, nothing else
"""

    try:
        client = get_gemini()
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        text = response.text.strip()
        # Strip markdown code fences if present
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
    cure_info = CURES_DB.get(top_class, {})

    # 2. Translate if non-English
    if language and language != "English":
        cure_info = translate_disease_info(top_class, cure_info, language)

    return {
        "disease": top_class,
        "confidence": confidence,
        "language": language,
        **cure_info
    }