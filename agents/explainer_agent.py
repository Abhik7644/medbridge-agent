from google import genai
import os, json, time
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def load_medicine_db():
    with open("data/medicines.json", "r") as f:
        return json.load(f)["medicines"]

def get_medicine_context(medicine_name: str) -> str:
    """[RAG retrieval] Pulls matching medicine info from local knowledge base."""
    db = load_medicine_db()
    for med in db:
        if (medicine_name.lower() in med["name"].lower() or
            any(medicine_name.lower() in alias.lower() for alias in med["aliases"])):
            return (
                f"Use: {med['use']}. "
                f"Side Effects: {med['side_effects']}. "
                f"Available at Jan Aushadhi: {med['available_at_jan_aushadhi']}."
            )
    return ""

def explain_and_format_pharmacy(medicine_name: str, language: str, pharmacy_list_text: str) -> dict:
    """
    [Explainer Agent]
    Single combined Gemini call: explains the medicine (RAG-grounded)
    AND formats real pharmacy data into friendly guidance.
    Combining these two tasks into one call keeps us under the
    free-tier daily request quota.
    """
    context = get_medicine_context(medicine_name)

    prompt = f"""
    Respond in {language}. You are a warm, friendly medical assistant
    helping a patient who may not have medical education.

    MEDICINE: {medicine_name}
    Known info: {context if context else "No exact match found — use general medical knowledge carefully."}

    REAL nearby pharmacies found via Google Places:
    {pharmacy_list_text}

    Give your answer in exactly two labeled sections:

    EXPLANATION:
    - What it's for (1 sentence)
    - How to take it
    - One important warning
    - Whether available at Jan Aushadhi (cheap govt store)
    (under 80 words total)

    PHARMACY:
    - Recommend which of the listed pharmacies to visit (or general guidance if none listed)
    - What to tell the pharmacist (mention asking for generic equivalent to save money)
    (under 80 words total)
    """

    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=prompt
            )
            text = response.text
            if "PHARMACY:" in text:
                explanation, pharmacy = text.split("PHARMACY:", 1)
                explanation = explanation.replace("EXPLANATION:", "").strip()
                pharmacy = pharmacy.strip()
            else:
                explanation, pharmacy = text.strip(), "Visit pmbjp.gov.in to find your nearest Jan Aushadhi Kendra."
            return {"explanation": explanation, "pharmacy_info": pharmacy}
        except Exception as e:
            if "RESOURCE_EXHAUSTED" in str(e) and attempt < 2:
                time.sleep(10)
            else:
                raise