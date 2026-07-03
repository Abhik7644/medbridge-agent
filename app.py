from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
import shutil, os, uuid
from agents.orchestrator import run_medbridge
from tools.pdf_generator import generate_pdf_report

app = FastAPI(title="MedBridge Agent")

# Serve the static CSS file at /static/style.css
app.mount("/static", StaticFiles(directory="static"), name="static")

REPORT_CACHE: dict[str, dict] = {}


def read_template(name: str) -> str:
    """Reads an HTML template from the templates/ folder."""
    with open(f"templates/{name}", "r", encoding="utf-8") as f:
        return f.read()


def build_medicines_html(medicines: list) -> str:
    html = ""
    for med in medicines:
        html += f"""
        <div class="med-card">
          <div class="med-header">
            <div class="med-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"/>
              </svg>
            </div>
            <div>
              <div class="med-name">{med['medicine']}</div>
              <div class="med-meta">
                <span class="badge">{med['dosage'] or 'unclear'}</span>
                <span class="badge">{med['frequency'] or 'unclear'}</span>
                <span class="badge">{med['duration'] or 'unclear'}</span>
              </div>
            </div>
          </div>
          <div class="med-body">
            <div class="med-section">
              <div class="section-label">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
                  <circle cx="12" cy="12" r="10"/>
                  <path d="M12 16v-4M12 8h.01"/>
                </svg>
                What is this medicine?
              </div>
              <div class="section-content">{med['explanation'] or 'No explanation available.'}</div>
            </div>
            <div class="med-section">
              <div class="section-label">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
                  <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
                  <polyline points="9 22 9 12 15 12 15 22"/>
                </svg>
                Where to buy
              </div>
              <div class="section-content">{med['pharmacy_info'] or 'Visit pmbjp.gov.in'}</div>
            </div>
            <div class="reminder-box">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
                <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
              </svg>
              <div>
                <strong>Set a reminder</strong> — {med['frequency'] or 'as prescribed'}<br>
                <span>Keep medicines visible · Complete the full course</span>
              </div>
            </div>
          </div>
        </div>
        """
    return html


def build_notes_html(result: dict) -> str:
    notes = result.get("doctor_notes", "")
    if not notes or notes.lower() in ("unclear", "", "none"):
        return ""
    return f"""
    <div class="notes-card">
      <div class="section-label" style="margin-bottom:8px;">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14 2 14 8 20 8"/>
        </svg>
        Doctor's notes
      </div>
      <div style="font-size:14px;color:#334155;line-height:1.6;">{notes}</div>
    </div>
    """


@app.get("/", response_class=HTMLResponse)
async def home():
    return read_template("home.html")


@app.post("/analyze", response_class=HTMLResponse)
async def analyze(
    file: UploadFile = File(...),
    location: str = Form(...),
    language: str = Form(...)
):
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    file.file.close()

    try:
        result = run_medbridge(temp_path, location, language)

        report_id = str(uuid.uuid4())[:8]
        REPORT_CACHE[report_id] = {
            "result": result,
            "location": location,
            "language": language,
        }
        if len(REPORT_CACHE) > 20:
            oldest_key = next(iter(REPORT_CACHE))
            REPORT_CACHE.pop(oldest_key)

        template = read_template("results.html")
        html = template.replace("{{total_medicines}}", str(result["total_medicines"]))
        html = html.replace("{{report_id}}", report_id)
        html = html.replace("{{notes_html}}", build_notes_html(result))
        html = html.replace("{{medicines_html}}", build_medicines_html(result["medicines"]))
        return html

    except Exception as e:
        error_page = """<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/static/style.css">
</head><body>
<div class="err-wrap">
  <div class="err-card">
    <h2>Something went wrong</h2>
    <p>__ERROR__</p>
    <p>If this is a quota error, wait a minute and try again.</p>
  </div>
  <br><a href="/">&#8592; Go back</a>
</div>
</body></html>"""
        return error_page.replace("__ERROR__", str(e))

    finally:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except PermissionError:
                pass


@app.get("/download/{report_id}")
async def download_report(report_id: str):
    cached = REPORT_CACHE.get(report_id)
    if not cached:
        return Response(
            content="Report not found or expired. Please analyze your prescription again.",
            status_code=404
        )
    pdf_bytes = generate_pdf_report(
        cached["result"], cached["location"], cached["language"]
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=medbridge_report.pdf"}
    )