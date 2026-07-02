import os, json, time, re
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

PRIMARY_MODEL  = "openai/gpt-oss-120b"
FALLBACK_MODEL = "qwen/qwen3.6-27b"

def load_medicine_db():
    with open("data/medicines.json", "r") as f:
        return json.load(f)["medicines"]

def get_medicine_context(medicine_name: str) -> str:
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

def call_groq(prompt: str, model: str) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=600,
        temperature=0.3
    )
    return response.choices[0].message.content

def explain_and_format_pharmacy(medicine_name: str, language: str, pharmacy_list_text: str) -> dict:
    context = get_medicine_context(medicine_name)

    # Use XML-style tags instead of JSON — much more reliable to parse
    prompt = f"""You are a warm friendly medical assistant. Respond in {language}.

MEDICINE: {medicine_name}
Known info: {context if context else "Use general medical knowledge carefully."}
Nearby pharmacies: {pharmacy_list_text}

Reply using EXACTLY these two XML tags and nothing else outside them:

<explanation>
What {medicine_name} is for in 1 simple sentence. How to take it. One important warning. Whether available at Jan Aushadhi govt store. Keep under 80 words. Do NOT use JSON or curly braces.
</explanation>

<pharmacy>
How to find this medicine. What to tell the pharmacist. Mention asking for generic equivalent to save 60-90% cost. Keep under 80 words. Do NOT use JSON or curly braces.
</pharmacy>"""

    for model in [PRIMARY_MODEL, FALLBACK_MODEL]:
        for attempt in range(2):
            try:
                raw = call_groq(prompt, model)

                # Extract using XML tag parsing — far more reliable than JSON
                exp_match = re.search(r'<explanation>(.*?)</explanation>', raw, re.DOTALL)
                pha_match = re.search(r'<pharmacy>(.*?)</pharmacy>', raw, re.DOTALL)

                explanation = exp_match.group(1).strip() if exp_match else ""
                pharmacy    = pha_match.group(1).strip() if pha_match else ""

                # If tags not found, try splitting on blank line as last resort
                if not explanation and not pharmacy:
                    parts = [p.strip() for p in raw.strip().split('\n\n') if p.strip()]
                    explanation = parts[0] if parts else raw.strip()
                    pharmacy    = parts[1] if len(parts) > 1 else "Visit pmbjp.gov.in or call 1800-180-8080"

                # Strip any accidental JSON artifacts
                explanation = re.sub(r'^\s*\{.*?"explanation"\s*:\s*"?', '', explanation, flags=re.DOTALL)
                explanation = explanation.strip('}"').strip()
                pharmacy    = pharmacy.strip('}"').strip()

                return {
                    "explanation": explanation or f"{medicine_name} is prescribed by your doctor. Ask your pharmacist for details.",
                    "pharmacy_info": pharmacy or "Visit pmbjp.gov.in or call Jan Aushadhi helpline 1800-180-8080 (free)."
                }

            except Exception as e:
                err = str(e)
                if "decommissioned" in err or "deprecated" in err or "model_not_active" in err:
                    break
                if attempt < 1:
                    time.sleep(5)

    return {
        "explanation": f"{medicine_name} is prescribed by your doctor. Please consult your pharmacist for detailed guidance.",
        "pharmacy_info": "Visit pmbjp.gov.in or call 1800-180-8080 to find your nearest Jan Aushadhi Kendra."
    }