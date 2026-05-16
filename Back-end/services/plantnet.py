import os
import requests
from dotenv import load_dotenv

load_dotenv()

PLANTNET_API_KEY = os.getenv("PLANTNET_API_KEY", "2b10eI1bAGWpNqWZB6FB9Tpu")
HEADERS          = {"User-Agent": "PlantVisionAI/1.0 (sushanthg851@gmail.com)"}

MIME_TYPES = {
    ".jpg":  "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png":  "image/png",
    ".webp": "image/webp",
    ".gif":  "image/gif",
    ".bmp":  "image/bmp",
}

def identify_plant(image_paths: list) -> tuple:
    if not image_paths:
        raise ValueError("No images provided")

    url    = "https://my-api.plantnet.org/v2/identify/all"
    params = {"api-key": PLANTNET_API_KEY, "lang": "en"}

    files  = []
    opened = []  # track open handles to close later

    try:
        for path in image_paths:
            ext  = os.path.splitext(path)[1].lower()
            mime = MIME_TYPES.get(ext, "image/jpeg")
            f    = open(path, "rb")
            opened.append(f)
            files.append(("images", (os.path.basename(path), f, mime)))

        response = requests.post(
            url,
            params=params,
            files=files,
            headers=HEADERS,
            timeout=30,
        )
        response.raise_for_status()

        data    = response.json()
        results = data.get("results", [])

        if not results:
            raise Exception("PlantNet could not identify any plant")

        top             = results[0]
        scientific_name = top["species"]["scientificNameWithoutAuthor"]
        confidence      = top["score"]

        return scientific_name, confidence

    finally:
        for f in opened:  # always close file handles
            f.close()