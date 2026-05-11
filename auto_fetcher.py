import requests
import pandas as pd

STATE_SLUGS = {
    "South Carolina": "south-carolina",
    "North Carolina": "north-carolina",
    "Georgia": "georgia",
    "Florida": "florida",
    "New York": "new-york",
    "Texas": "texas",
    "Virginia": "virginia",
    "Michigan": "michigan",
    "Ohio": "ohio",
    "Pennsylvania": "pennsylvania",
    "California": "california"
}

def fetch_lotteryusa_results(state_slug):
    url = f"https://www.lotteryusa.com/{state_slug}/pick-3/"

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()

        # Simple fallback structure
        # If website blocks scraping, user can upload CSV manually.
        return pd.DataFrame(columns=["date", "number"])

    except Exception:
        return pd.DataFrame(columns=["date", "number"])
