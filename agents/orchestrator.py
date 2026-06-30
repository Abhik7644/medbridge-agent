from agents.prescription_agent import extract_medicines_from_prescription
from agents.explainer_agent import explain_medicine
from agents.pharmacy_agent import find_nearby_pharmacies, set_followup_reminder

def run_medbridge(image_path: str, location: str, language: str = "English") -> dict:
    """
    Main orchestrator — coordinates all 3 agents
    to produce a complete patient report.
    """
    print("🔍 Step 1: Reading your prescription...")
    prescription_data = extract_medicines_from_prescription(image_path)
    
    medicines = prescription_data.get("medicines", [])
    results = []
    
    for med in medicines:
        name = med.get("name", "Unknown")
        print(f"💊 Step 2: Explaining {name}...")
        
        explanation = explain_medicine(name, language)
        
        print(f"🗺️ Step 3: Finding pharmacy for {name}...")
        pharmacy_info = find_nearby_pharmacies(location, name)
        
        reminder = set_followup_reminder(
            name, 
            med.get("frequency", "as prescribed")
        )
        
        results.append({
            "medicine": name,
            "dosage": med.get("dosage"),
            "frequency": med.get("frequency"),
            "duration": med.get("duration"),
            "explanation": explanation,
            "pharmacy_info": pharmacy_info,
            "reminder": reminder
        })
    
    return {
        "doctor_notes": prescription_data.get("doctor_notes", ""),
        "medicines": results,
        "total_medicines": len(results)
    }