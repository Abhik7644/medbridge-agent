from google import genai
import json, os
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def load_medicine_db():
    with open("data/medicines.json", "r") as f:
        return json.load(f)["medicines"]

def explain_medicine(medicine_name: str, language: str = "English") -> str:
    db = load_medicine_db()
    context = ""
    for med in db:
        if (medicine_name.lower() in med["name"].lower() or
            any(medicine_name.lower() in alias.lower() for alias in med["aliases"])):
            context = f"""
            Medicine: {med['name']}
            Use: {med['use']}
            Side Effects: {med['side_effects']}
            Simple Explanation: {med['simple_explanation']}
            Available at Jan Aushadhi: {med['available_at_jan_aushadhi']}
            """
            break

    prompt = f"""
    You are a friendly medical assistant explaining medicines to patients 
    in simple, non-technical language in {language}.

    Context from medical database:
    {context if context else "No exact match found, use general knowledge carefully."}

    Explain the medicine "{medicine_name}" to a patient who may not have 
    medical education. Include:
    1. What it's for (in one simple sentence)
    2. How to take it (timing with food etc.)
    3. One important warning
    4. Whether it's available at Jan Aushadhi store (cheaper govt option)

    Keep it under 100 words. Be warm and reassuring.
    Respond in {language}.
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text