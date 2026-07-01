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

def call_groq(prompt: str, model: str) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=600,
        temperature=0.3
    )
    return response.choices[0].message.content

def explain_and_format_pharmacy(medicine_name: str, language: str, pharmacy_list_text: str) -> dict:
    """
    [Explainer Agent] Uses JSON output format for reliable parsing.
    RAG-grounded explanation + pharmacy guidance in one Groq call.
    """
    context = get_medicine_context(medicine_name)

    prompt = f"""You are a warm friendly medical assistant. Respond in {language}.

MEDICINE: {medicine_name}
Known info: {context if context else "Use general medical knowledge carefully."}
Nearby pharmacies: {pharmacy_list_text}

Return ONLY a valid JSON object, no markdown, no extra text:
{{
  "explanation": "What {medicine_name} is for in 1 sentence. How to take it. One important warning. Whether available at Jan Aushadhi govt store. Under 80 words.",
  "pharmacy_info": "Which pharmacy to visit or how to find one. What to tell the pharmacist. Mention asking for generic equivalent to save money. Under 80 words."
}}"""

    for model in [PRIMARY_MODEL, FALLBACK_MODEL]:
        for attempt in range(2):
            try:
                raw = call_groq(prompt, model)
                # Strip markdown fences if present
                raw = re.sub(r"```json|```", "", raw).strip()
                # Extract JSON object
                json_match = re.search(r'\{.*\}', raw, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group())
                    return {
                        "explanation": parsed.get("explanation", "").strip(),
                        "pharmacy_info": parsed.get("pharmacy_info", "").strip()
                    }
                # If JSON parse failed, try splitting on newlines as last resort
                lines = [l.strip() for l in raw.split('\n') if l.strip()]
                return {
                    "explanation": lines[0] if lines else raw,
                    "pharmacy_info": lines[1] if len(lines) > 1 else "Visit pmbjp.gov.in"
                }
            except Exception as e:
                err = str(e)
                if "decommissioned" in err or "deprecated" in err:
                    break  # try fallback model
                if attempt < 1:
                    time.sleep(5)

    return {
        "explanation": f"{medicine_name} is a medicine prescribed by your doctor. Please consult your pharmacist for details.",
        "pharmacy_info": "Visit pmbjp.gov.in or call 1800-180-8080 to find your nearest Jan Aushadhi Kendra."
    }