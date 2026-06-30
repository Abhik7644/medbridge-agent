import googlemaps
import os
from dotenv import load_dotenv

load_dotenv()
gmaps = googlemaps.Client(key=os.getenv("MAPS_API_KEY"))

def search_real_pharmacies(location: str) -> list:
    """
    [Tool] Real call to Google Places API — finds actual nearby
    pharmacies/Jan Aushadhi stores. Returns [] on failure so the
    agent can gracefully fall back to general guidance.
    """
    try:
        geocode_result = gmaps.geocode(location)
        if not geocode_result:
            return []
        lat_lng = geocode_result[0]["geometry"]["location"]

        places_result = gmaps.places_nearby(
            location=lat_lng,
            radius=3000,
            keyword="Jan Aushadhi pharmacy medical store",
            type="pharmacy"
        )

        pharmacies = []
        for place in places_result.get("results", [])[:5]:
            pharmacies.append({
                "name": place.get("name"),
                "address": place.get("vicinity"),
                "rating": place.get("rating", "N/A"),
                "open_now": place.get("opening_hours", {}).get("open_now", "Unknown")
            })
        return pharmacies
    except Exception as e:
        print(f"⚠️ [Pharmacy Agent] Maps API error: {e}")
        return []


def format_pharmacy_list(pharmacies: list) -> str:
    """Converts pharmacy results into plain text for prompting."""
    if not pharmacies:
        return "No live pharmacy data available. Suggest checking pmbjp.gov.in for the nearest Jan Aushadhi Kendra."
    return "\n".join([
        f"- {p['name']} ({p['address']}) — Rating: {p['rating']}, Open now: {p['open_now']}"
        for p in pharmacies
    ])