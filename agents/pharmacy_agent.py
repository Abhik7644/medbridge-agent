from tools.pharmacy_finder import search_real_pharmacies, format_pharmacy_list

def get_pharmacy_context(location: str) -> tuple[list, str]:
    """
    [Pharmacy Agent]
    Real tool call to Google Places API to find nearby pharmacies.
    Returns both raw results (for the activity log) and formatted text
    (for the Explainer Agent's prompt).
    """
    pharmacies = search_real_pharmacies(location)
    formatted = format_pharmacy_list(pharmacies)
    return pharmacies, formatted

def set_followup_reminder(medicine_name: str, frequency: str) -> str:
    """Generates a reminder message for the patient."""
    return f"""
    ⏰ REMINDER SET for {medicine_name}
    Frequency: {frequency}
    
    Tips:
    - Set an alarm on your phone matching this schedule
    - Keep medicines at a visible place (not bathroom — too humid)
    - Never stop antibiotics early even if feeling better
    - Consult doctor if you experience unusual symptoms
    """