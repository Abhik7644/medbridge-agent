from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def find_nearby_pharmacies(location: str, medicine_name: str) -> str:
    prompt = f"""
    A patient in {location} needs to find "{medicine_name}".

    Provide helpful guidance on:
    1. How to find the nearest Jan Aushadhi Kendra 
       (government cheap medicine store) — mention pmbjp.gov.in
    2. What to tell the pharmacist
    3. Expected price range for generic vs branded version
    4. Tip: ask for generic equivalent to save money

    Be practical and specific. Keep under 150 words.
    """
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text

def set_followup_reminder(medicine_name: str, frequency: str) -> str:
    return f"""
    ⏰ REMINDER SET for {medicine_name}
    Frequency: {frequency}
    
    Tips:
    - Set an alarm on your phone matching this schedule
    - Keep medicines at a visible place (not bathroom — too humid)
    - Never stop antibiotics early even if feeling better
    - Consult doctor if you experience unusual symptoms
    """