# Maps API removed — replaced with structured static guidance
# This avoids billing requirements while still giving patients
# actionable, location-aware pharmacy information.

HELPLINE = "1800-180-8080"
PMBJP_URL = "pmbjp.gov.in"

def search_real_pharmacies(location: str) -> list:
    """
    Maps API removed to avoid billing requirement.
    Returns empty list — guidance handled by format_pharmacy_list.
    """
    return []

def format_pharmacy_list(pharmacies: list, location: str = "") -> str:
    """
    Returns structured guidance for finding Jan Aushadhi stores.
    Location-aware: includes city name in search suggestion.
    """
    city = location.split(",")[0].strip() if location else "your city"
    return (
        f"No live pharmacy data. Guide patient to:\n"
        f"1. Visit {PMBJP_URL} → Store Locator → search '{city}'\n"
        f"2. Search 'Jan Aushadhi Kendra {city}' on Google Maps\n"
        f"3. Call Jan Aushadhi helpline: {HELPLINE} (free, toll-free)\n"
        f"4. Ask any pharmacist for the generic equivalent to save 60-90% cost"
    )