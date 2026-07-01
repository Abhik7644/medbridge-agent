# 🏥 MedBridge Agent

An AI agent that helps patients in low-resource areas understand 
their prescriptions and find affordable nearby pharmacies.

## Architecture
- **Prescription Agent** — Gemini Vision OCR extracts medicines
- **Pharmacy Agent** — Google Places API finds real nearby pharmacies  
- **Explainer Agent** — RAG + Gemini explains medicines simply
- **Orchestrator** — Coordinates all agents with visible reasoning trace

## Setup
1. Clone the repo
2. Create venv: `python -m venv venv && venv\Scripts\activate`
3. Install deps: `pip install -r requirements.txt`
4. Add `.env` file:
GEMINI_API_KEY=your_key
MAPS_API_KEY=your_key
5. Run: `uvicorn app:app --reload`

## Key Features
- Prescription image OCR via Gemini Vision
- Real pharmacy search via Google Places API
- RAG-grounded medicine explanations
- Downloadable PDF report
- Visible agent activity log
- Security: images deleted immediately, no data stored

## Tech Stack
- Google Gemini 2.5 Flash Lite
- FastAPI + Uvicorn
- Google Places API
- ReportLab (PDF generation)
- Python 3.11