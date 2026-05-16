import requests

HEADERS = {"User-Agent": "PlantVisionAI/1.0 (sushanthg851@gmail.com)"}

def get_gbif_data(scientific_name: str):
    url    = "https://api.gbif.org/v1/species/search"
    params = {"q": scientific_name}

    res = requests.get(url, params=params, headers=HEADERS)
    res.raise_for_status()
    data = res.json()

    if data["results"]:
        return data["results"][0].get("family", "Not available")
    return "Not available"


def get_wikipedia_description(scientific_name: str):
    search_url = "https://en.wikipedia.org/w/api.php"

    res = requests.get(search_url, params={
        "action":   "query",
        "list":     "search",
        "srsearch": scientific_name,
        "format":   "json"
    }, headers=HEADERS)

    if res.status_code != 200 or not res.json()["query"]["search"]:
        return None, None

    title       = res.json()["query"]["search"][0]["title"]
    summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title.replace(' ', '_')}"
    res2        = requests.get(summary_url, headers=HEADERS)

    if res2.status_code == 200:
        return title, res2.json().get("extract")
    return title, None