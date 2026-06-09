import requests

HEADERS = {
    "User-Agent": "PlantApp/1.0 (sushanthg851@gmail.com)"
}

INDIAN_LANGS = {
    "hi": "Hindi",
    "kn": "Kannada",
    "ta": "Tamil",
    "te": "Telugu",
    "ml": "Malayalam",
    "mr": "Marathi",
    "bn": "Bengali",
    "gu": "Gujarati",
    "pa": "Punjabi",
    "ur": "Urdu"
}


# ─────────────────────────────────────────
# STEP 1: Identify plant using PlantNet
# ─────────────────────────────────────────
def identify_plant(image_paths):
    url = "https://my-api.plantnet.org/v2/identify/all"
    params = {"api-key": "2b10eI1bAGWpNqWZB6FB9Tpu"}

    files = [("images", open(path, "rb")) for path in image_paths]

    response = requests.post(url, params=params, files=files)
    response.raise_for_status()
    data = response.json()

    top = data["results"][0]
    scientific_name = top["species"]["scientificNameWithoutAuthor"]
    confidence = top["score"]

    print(f"\n🌿 Plant Identified: {scientific_name}")
    print(f"   Confidence: {confidence:.2%}")

    return scientific_name, confidence  


# ─────────────────────────────────────────
# STEP 2: Get family from GBIF
# ─────────────────────────────────────────
def get_gbif_data(scientific_name):
    url = "https://api.gbif.org/v1/species/search"
    params = {"q": scientific_name}

    res = requests.get(url, params=params, headers=HEADERS)
    res.raise_for_status()
    data = res.json()

    if data["results"]:
        plant_data = data["results"][0]
        family = plant_data.get("family", "Not available")
        print(f"   Family: {family}")
        return family
    else:
        print("   No GBIF data found")
        return None


# ─────────────────────────────────────────
# STEP 3: Get Wikipedia description
# ─────────────────────────────────────────
def get_wikipedia_description(scientific_name):
    search_url = "https://en.wikipedia.org/w/api.php"

    # Search for the page
    res = requests.get(search_url, params={
        "action": "query",
        "list": "search",
        "srsearch": scientific_name,
        "format": "json"
    }, headers=HEADERS)

    if res.status_code != 200 or not res.json()["query"]["search"]:
        print("   No Wikipedia result found")
        return None, None

    title = res.json()["query"]["search"][0]["title"]

    # Get summary
    summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title.replace(' ', '_')}"
    res2 = requests.get(summary_url, headers=HEADERS)

    description = None
    if res2.status_code == 200:
        description = res2.json().get("extract")
        print(f"\n📖 Description:\n   {description}")
    else:
        print("   Summary not available")

    return title, description


# ─────────────────────────────────────────
# STEP 4: Get local/Indian language names
#         from Wikipedia + Wikidata
# ─────────────────────────────────────────
def get_local_names(scientific_name, wiki_title=None):
    indian_names = {}

    # --- Source A: Wikipedia langlinks ---
    if wiki_title:
        search_url = "https://en.wikipedia.org/w/api.php"
        lang_res = requests.get(search_url, params={
            "action": "query",
            "prop": "langlinks",
            "titles": wiki_title,
            "lllimit": "50",
            "format": "json"
        }, headers=HEADERS)

        if lang_res.status_code == 200:
            pages = lang_res.json()["query"]["pages"]
            for page_id in pages:
                for lang in pages[page_id].get("langlinks", []):
                    code = lang["lang"]
                    if code in INDIAN_LANGS:
                        indian_names[code] = lang["*"]

    # --- Source B: Wikidata labels (fills missing languages) ---
    clean_name = scientific_name.replace("_", " ").strip()
    search_url = "https://www.wikidata.org/w/api.php"

    res = requests.get(search_url, params={
        "action": "wbsearchentities",
        "search": clean_name,
        "language": "en",
        "format": "json",
        "limit": 5
    }, headers=HEADERS)

    entity_id = None
    labels = {}

    if res.status_code == 200:
        results = res.json().get("search", [])

        # Try to find entity with matching P225 taxon name
        for result in results:
            candidate_id = result["id"]
            entity_url = f"https://www.wikidata.org/wiki/Special:EntityData/{candidate_id}.json"
            entity_data = requests.get(entity_url, headers=HEADERS).json()
            entity = entity_data["entities"][candidate_id]

            claims = entity.get("claims", {})
            for claim in claims.get("P225", []):
                taxon_value = (
                    claim.get("mainsnak", {})
                         .get("datavalue", {})
                         .get("value", "")
                )
                if taxon_value.lower() == clean_name.lower():
                    entity_id = candidate_id
                    labels = entity.get("labels", {})
                    break
            if entity_id:
                break

        # Fallback to first result if no P225 match
        if not entity_id and results:
            entity_id = results[0]["id"]
            entity_url = f"https://www.wikidata.org/wiki/Special:EntityData/{entity_id}.json"
            entity_data = requests.get(entity_url, headers=HEADERS).json()
            labels = entity_data["entities"][entity_id].get("labels", {})

    # Merge Wikidata labels into missing Indian language slots
    for code in INDIAN_LANGS:
        if code not in indian_names and code in labels:
            indian_names[code] = labels[code]["value"]

    # Also grab English name from Wikidata if available
    english_name = labels.get("en", {}).get("value", "Not available")

    # ── Print results ──
    print(f"\n🌍 Local Names:")
    print(f"   {'English':12}: {english_name}")
    for code, lang_name in INDIAN_LANGS.items():
        value = indian_names.get(code, "Not available")
        print(f"   {lang_name:12}: {value}")

    return {
        "english": english_name,
        **{INDIAN_LANGS[code].lower(): indian_names.get(code, "Not available")
           for code in INDIAN_LANGS}
    }


# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────
if __name__ == "__main__":
    image_paths = [
        "Front-end/hib1.jpg",
        "Front-end/hib2.jpg"
    ]

    scientific_name = identify_plant(image_paths)
    family          = get_gbif_data(scientific_name)
    wiki_title, desc = get_wikipedia_description(scientific_name)
    names           = get_local_names(scientific_name, wiki_title)