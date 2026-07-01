import os, json, time
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def load_medicine_db():
    with open("data/medicines.json", "r") as f:
        return json.load(f)["medicines"]

def get_medicine_context(medicine_name: str) -> str:
    """[RAG retrieval] Pulls matching medicine from local knowledge base."""
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
    Single Groq call: explains medicine (RAG-grounded) AND
    formats real pharmacy data into friendly patient guidance.
    """
    context = get_medicine_context(medicine_name)

    prompt = f"""
    Respond in {language}. You are a warm, friendly medical assistant
    helping a patient who may not have medical education.

    MEDICINE: {medicine_name}
    Known info: {context if context else "No exact match — use general medical knowledge carefully."}

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
    - Recommend which listed pharmacy to visit (or general guidance if none listed)
    - What to tell the pharmacist (mention asking for generic equivalent)
    (under 80 words total)
    """

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.3
            )
            text = response.choices[0].message.content
            if "PHARMACY:" in text:
                explanation, pharmacy = text.split("PHARMACY:", 1)
                explanation = explanation.replace("EXPLANATION:", "").strip()
                pharmacy = pharmacy.strip()
            else:
                explanation = text.strip()
                pharmacy = "Visit pmbjp.gov.in to find your nearest Jan Aushadhi Kendra."
            return {"explanation": explanation, "pharmacy_info": pharmacy}
        except Exception as e:
            if attempt < 2:
                time.sleep(5)
            else:
                raise