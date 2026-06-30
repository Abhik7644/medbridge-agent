from google import genai
from google.genai import types
import os, json, re
from PIL import Image
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def extract_medicines_from_prescription(image_path: str) -> dict:
    with Image.open(image_path) as img:
      image =img.copy()

    prompt = """
    You are a medical prescription reader. 
    Extract all medicines from this prescription image.
    Return ONLY a JSON object in this format:
    {
        "medicines": [
            {
                "name": "medicine name",
                "dosage": "e.g. 500mg",
                "frequency": "e.g. twice daily",
                "duration": "e.g. 5 days"
            }
        ],
        "doctor_notes": "any additional notes"
    }
    If you cannot read something clearly, write "unclear".
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[prompt, image]
    )

    raw = response.text
    json_match = re.search(r'\{.*\}', raw, re.DOTALL)
    if json_match:
        return json.loads(json_match.group())
    return {"medicines": [], "doctor_notes": raw}