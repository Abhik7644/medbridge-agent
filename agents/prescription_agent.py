import os, json, re
import pytesseract
from PIL import Image, ImageFilter, ImageEnhance
from dotenv import load_dotenv

load_dotenv()

# Set Tesseract path for Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def preprocess_image(image_path: str) -> Image.Image:
    """
    Preprocesses prescription image for better OCR accuracy.
    Converts to grayscale, increases contrast, sharpens.
    """
    with Image.open(image_path) as img:
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img = img.convert("L")  # grayscale
        img = ImageEnhance.Contrast(img).enhance(2.0)
        img = img.filter(ImageFilter.SHARPEN)
        return img.copy()

def extract_medicines_from_prescription(image_path: str) -> dict:
    """
    [Prescription Agent]
    Uses Tesseract OCR (local, no API) to extract raw text
    from prescription image, then uses Groq to parse it into
    structured medicine data.
    """
    from groq import Groq
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    # Step 1: Local OCR — extract raw text from image
    image = preprocess_image(image_path)
    raw_text = pytesseract.image_to_string(image)
    print("📝 [Prescription Agent] OCR complete, parsing with Groq...")

    if not raw_text.strip():
        return {"medicines": [], "doctor_notes": "Could not read prescription image clearly."}

    # Step 2: Groq parses the OCR text into structured JSON
    prompt = f"""
    You are a medical prescription parser.
    Below is raw OCR text extracted from a prescription image.
    Extract all medicines and return ONLY a valid JSON object.

    OCR TEXT:
    {raw_text}

    Return ONLY this JSON format, no extra text:
    {{
        "medicines": [
            {{
                "name": "medicine name",
                "dosage": "e.g. 500mg",
                "frequency": "e.g. twice daily",
                "duration": "e.g. 5 days"
            }}
        ],
        "doctor_notes": "any additional notes or instructions"
    }}

    If a field is unclear, write "unclear".
    """

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                temperature=0.1
            )
            raw = response.choices[0].message.content
            raw = re.sub(r"```json|```", "", raw).strip()
            json_match = re.search(r'\{.*\}', raw, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            return {"medicines": [], "doctor_notes": raw}
        except Exception as e:
            err = str(e)
            if ("decommissioned" in err or "deprecated" in err):
                # try fallback model
                try:
                    response = client.chat.completions.create(
                        model="qwen/qwen3.6-27b",
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=800,
                        temperature=0.1
                    )
                    raw = response.choices[0].message.content
                    raw = re.sub(r"```json|```", "", raw).strip()
                    json_match = re.search(r'\{.*\}', raw, re.DOTALL)
                    if json_match:
                        return json.loads(json_match.group())
                except:
                    pass
            if attempt < 2:
                import time
                time.sleep(5)
            else:
                raise