import requests

HEADERS = {"User-Agent": "PlantVisionAI/1.0 (sushanthg851@gmail.com)"}

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

def get_local_names(scientific_name: str, wiki_title: str = None):
    clean_name   = scientific_name.replace("_", " ").strip()
    indian_names = {}

    # Source A: Wikipedia langlinks
    if wiki_title:
        search_url = "https://en.wikipedia.org/w/api.php"
        lang_res = requests.get(search_url, params={
            "action": "query",
            "prop":   "langlinks",
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

    # Source B: Wikidata labels
    res = requests.get("https://www.wikidata.org/w/api.php", params={
        "action":   "wbsearchentities",
        "search":   clean_name,
        "language": "en",
        "format":   "json",
        "limit":    5
    }, headers=HEADERS)

    labels    = {}
    entity_id = None

    if res.status_code == 200:
        results = res.json().get("search", [])
        for result in results:
            candidate_id  = result["id"]
            entity_url    = f"https://www.wikidata.org/wiki/Special:EntityData/{candidate_id}.json"
            entity_data   = requests.get(entity_url, headers=HEADERS).json()
            entity        = entity_data["entities"][candidate_id]
            for claim in entity.get("claims", {}).get("P225", []):
                taxon_value = (
                    claim.get("mainsnak", {})
                         .get("datavalue", {})
                         .get("value", "")
                )
                if taxon_value.lower() == clean_name.lower():
                    entity_id = candidate_id
                    labels    = entity.get("labels", {})
                    break
            if entity_id:
                break

        if not entity_id and results:
            entity_id   = results[0]["id"]
            entity_url  = f"https://www.wikidata.org/wiki/Special:EntityData/{entity_id}.json"
            entity_data = requests.get(entity_url, headers=HEADERS).json()
            labels      = entity_data["entities"][entity_id].get("labels", {})

    # Merge Wikidata into missing slots
    for code in INDIAN_LANGS:
        if code not in indian_names and code in labels:
            indian_names[code] = labels[code]["value"]

    return {
        "english": labels.get("en", {}).get("value", "Not available"),
        **{INDIAN_LANGS[code].lower(): indian_names.get(code, "Not available")
           for code in INDIAN_LANGS}
    }