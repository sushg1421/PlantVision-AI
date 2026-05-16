from fastapi import APIRouter, UploadFile, File
from typing import List
from services.plantnet import identify_plant
from services.wikipedia import get_local_names
from services.gbif import get_gbif_data
from services.gbif import get_wikipedia_description
import tempfile, os

router = APIRouter()

@router.post("/identify")
async def identify(images: List[UploadFile] = File(...)):
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