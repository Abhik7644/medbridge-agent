import time
from agents.prescription_agent import extract_medicines_from_prescription
from agents.explainer_agent import explain_and_format_pharmacy
from agents.pharmacy_agent import get_pharmacy_context, set_followup_reminder

def run_medbridge(image_path: str, location: str, language: str = "English") -> dict:
    """
    [Orchestrator Agent]
    Coordinates Prescription Agent -> Pharmacy Agent (tool) -> Explainer Agent
    for each medicine, and logs a visible reasoning trace.
    """
    trace = []
    trace.append({"agent": "Orchestrator", "action": "Received prescription image", "status": "started"})
    print("🔒 [Security] Processing prescription in-memory — no patient data will be persisted")

    print("🔍 [Prescription Agent] Reading image with Gemini Vision OCR...")
    prescription_data = extract_medicines_from_prescription(image_path)
    trace.append({
        "agent": "Prescription Agent",
        "action": f"Extracted {len(prescription_data.get('medicines', []))} medicines via OCR",
        "status": "complete"
    })

    medicines = prescription_data.get("medicines", [])
    results = []

    # Fetch pharmacy data ONCE per location (not per medicine) — saves API calls
    trace.append({"agent": "Pharmacy Agent", "action": f"Calling Google Places API near {location}", "status": "running"})
    pharmacies_raw, pharmacy_list_text = get_pharmacy_context(location)
    trace.append({
        "agent": "Pharmacy Agent",
        "action": f"Found {len(pharmacies_raw)} real pharmacies via Google Places" if pharmacies_raw
                   else "No live pharmacy data (fallback guidance used)",
        "status": "complete"
    })

    for med in medicines:
        name = med.get("name", "Unknown")

        trace.append({"agent": "Explainer Agent", "action": f"Generating explanation + pharmacy guidance for {name}", "status": "running"})
        combined = explain_and_format_pharmacy(name, language, pharmacy_list_text)
        trace.append({"agent": "Explainer Agent", "action": f"Completed {name}", "status": "complete"})

        reminder = set_followup_reminder(name, med.get("frequency", "as prescribed"))

        results.append({
            "medicine": name,
            "dosage": med.get("dosage"),
            "frequency": med.get("frequency"),
            "duration": med.get("duration"),
            "explanation": combined["explanation"],
            "pharmacy_info": combined["pharmacy_info"],
            "reminder": reminder
        })
        time.sleep(2)  # small buffer to respect rate limits

    trace.append({"agent": "Orchestrator", "action": "All agents completed", "status": "done"})

    return {
        "doctor_notes": prescription_data.get("doctor_notes", ""),
        "medicines": results,
        "total_medicines": len(results),
        "pharmacies_found": pharmacies_raw,
        "agent_trace": trace
    }