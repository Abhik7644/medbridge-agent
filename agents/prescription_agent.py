import os, json, re, time, base64
from groq import Groq
from PIL import Image
from dotenv import load_dotenv
import io

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def image_to_base64(image_path: str) -> str:
    """Convert image to base64 string for Groq vision API."""
    with Image.open(image_path) as img:
        # Convert to RGB if needed (handles PNG with transparency)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

def extract_medicines_from_prescription(image_path: str) -> dict:
    """
    [Prescription Agent]
    Uses Groq LLaMA Vision to read prescription image and
    extract structured medicine data.
    """
    image_b64 = image_to_base64(image_path)

    prompt = """
    You are a medical prescription reader.
    Extract all medicines from this prescription image.
    Return ONLY a valid JSON object in this exact format:
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
    Return ONLY the JSON, no extra text.
    """

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model="llama-3.2-11b-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_b64}"
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ],
                max_tokens=1000,
                temperature=0.1
            )
            raw = response.choices[0].message.content
            # Strip markdown code fences if present
            raw = re.sub(r"```json|```", "", raw).strip()
            json_match = re.search(r'\{.*\}', raw, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {"medicines": [], "doctor_notes": raw}
        except Exception as e:
            if attempt < 2:
                time.sleep(5)
            else:
                raise