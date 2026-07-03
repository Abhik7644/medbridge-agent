# MedBridge Agent

> An AI agent that helps patients in low-resource areas understand their prescriptions and find affordable medicines.

## Problem
Millions of patients leave hospital visits with prescriptions they cannot understand. Medical jargon, handwriting, and language barriers leave patients confused about what medicines to take and where to buy affordable alternatives.

## Solution
MedBridge is a multi-agent AI system that:
- Reads prescription images using OCR
- Explains each medicine in simple language (English or Hindi)
- Guides patients to affordable Jan Aushadhi government pharmacies
- Generates a downloadable PDF report

## Architecture
User uploads prescription image
│
▼
[Orchestrator Agent]
│
┌────┴───────────────┐
▼                    ▼
[Prescription Agent]  [Pharmacy Agent]
Tesseract OCR         Jan Aushadhi guidance

Groq parsing        (location-aware)
│
▼
[Explainer Agent]
RAG + Groq LLM
medicine explanations


## Key Concepts Used (from course)
- Multi-agent system with orchestration
- RAG (Retrieval Augmented Generation) over medicine knowledge base
- Tool use (Google Places API integration)
- Security (PII not stored, images deleted immediately)
- Deployability (FastAPI + Cloud Run ready)

## Tech Stack
- Groq (`openai/gpt-oss-120b`) — text generation
- Tesseract OCR — local prescription reading
- FastAPI + Uvicorn — web server
- ReportLab — PDF generation
- Google Places API — pharmacy search (optional)

## Setup

### Prerequisites
- Python 3.10+
- Tesseract OCR installed: https://github.com/UB-Mannheim/tesseract/wiki

### Installation
```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/medbridge-agent.git
cd medbridge-agent

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables
Create a `.env` file in the root:
GROQ_API_KEY=your_groq_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
MAPS_API_KEY=your_maps_api_key_here

Get your free Groq API key at: https://console.groq.com

### Run
```bash
uvicorn app:app --reload
```
Open http://127.0.0.1:8000 in your browser.

## 📁 Project Structure

```text
medbridge-agent/
│
├── app.py                      # FastAPI web server
├── requirements.txt
│
├── agents/
│   ├── orchestrator.py         # Coordinates all agents
│   ├── prescription_agent.py   # OCR + Groq parsing
│   ├── explainer_agent.py      # Medicine explanation
│   └── pharmacy_agent.py       # Pharmacy guidance
│
├── tools/
│   ├── pharmacy_finder.py      # Google Places API
│   └── pdf_generator.py        # PDF report generation
│
├── data/
│   └── medicines.json          # Local medicine knowledge
│
├── static/
│   └── style.css               # Frontend styles
│
└── templates/
    ├── home.html               # Upload page
    └── results.html            # Results page
```

## Security
- Prescription images are processed in-memory only
- Images are deleted immediately after OCR processing
- No patient data, prescription content, or personal information is stored
- All API keys stored in `.env` (never committed to git)

## Demo
[YouTube Demo Link]

## Track
Agents for Good — Kaggle 5-Day AI Agents Intensive Course 2026

## Disclaimer
This tool is for informational purposes only and does not replace professional medical advice.
EOF
