# disease_router.py

import tensorflow as tf
import json, numpy as np
from fastapi import APIRouter, UploadFile
from PIL import Image
import io, os

router = APIRouter(prefix="/disease", tags=["disease"])

model = None  # ← don't load at startup

def get_model():
    global model
    if model is None:
        model_path = "models/disease_model.h5"
        if not os.path.exists(model_path):
            raise FileNotFoundError("Disease model not trained yet. Run ml/train.py first.")
        model = tf.keras.models.load_model(model_path)
    return model

with open("data/disease_cures.json") as f:
    CURES_DB = json.load(f)

with open("models/disease_classes.json") as f:
    CLASS_NAMES = json.load(f)  # fill this after training

@router.post("/detect")
async def detect_disease(file: UploadFile):
    m = get_model()  # ← loads only when this endpoint is called
    img = Image.open(io.BytesIO(await file.read())).resize((224, 224))
    arr = np.expand_dims(np.array(img) / 255.0, 0)
    preds = m.predict(arr)[0]
    top_class = CLASS_NAMES[np.argmax(preds)]
    confidence = float(np.max(preds))
    cure_info = CURES_DB.get(top_class, {})
    return {"disease": top_class, "confidence": confidence, **cure_info}