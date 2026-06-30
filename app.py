from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, Response
import shutil, os, uuid
from agents.orchestrator import run_medbridge
from tools.pdf_generator import generate_pdf_report

app = FastAPI(title="MedBridge Agent")

# Simple in-memory store for the last few reports (demo-scale, not production DB)
REPORT_CACHE: dict[str, dict] = {}

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <html>
    <head>
        <title>MedBridge 🏥</title>
        <style>
            body { font-family: Arial; max-width: 600px; 
                   margin: 50px auto; padding: 20px; }
            h1 { color: #2c7a7b; }
            input, select { width: 100%; padding: 10px; 
                           margin: 10px 0; border-radius: 5px;
                           border: 1px solid #ccc; box-sizing: border-box; }
            label { font-weight: bold; }
            button { background: #2c7a7b; color: white; 
                    padding: 12px 30px; border: none; 
                    border-radius: 5px; cursor: pointer; 
                    font-size: 16px; width: 100%; margin-top: 10px; }
            button:hover { background: #236363; }
            .security-note { background: #fff3cd; padding: 10px; 
                              border-radius: 5px; font-size: 13px; 
                              margin-top: 15px; }
        </style>
    </head>
    <body>
        <h1>🏥 MedBridge Agent</h1>
        <p>Upload your prescription to understand your medicines 
           and find nearby pharmacies.</p>
        <form action="/analyze" method="post" 
              enctype="multipart/form-data">
            <label>Upload Prescription Image:</label>
            <input type="file" name="file" accept="image/*" required>
            <label>Your Location (City/Area):</label>
            <input type="text" name="location" 
                   placeholder="e.g. Patna, Bihar" required>
            <label>Language:</label>
            <select name="language">
                <option>English</option>
                <option>Hindi</option>
            </select>
            <button type="submit">Analyze Prescription 🔍</button>
        </form>
        <div class="security-note">
            🔒 Your prescription image is processed in-memory and deleted 
            immediately after analysis. No personal data is stored.
        </div>
    </body>
    </html>
    """


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

        # Cache result so /download/{id} can regenerate the PDF
        report_id = str(uuid.uuid4())[:8]
        REPORT_CACHE[report_id] = {
            "result": result,
            "location": location,
            "language": language,
        }
        # Keep cache small — drop oldest if it grows too large
        if len(REPORT_CACHE) > 20:
            oldest_key = next(iter(REPORT_CACHE))
            REPORT_CACHE.pop(oldest_key)

        trace_html = """
        <div style="background:#1a1a2e;color:#0f0;padding:15px;
                    border-radius:8px;font-family:monospace;
                    margin-bottom:20px;font-size:13px;
                    max-height:250px;overflow-y:auto;">
        <b>🤖 Agent Activity Log</b><br><br>
        """
        for step in result.get("agent_trace", []):
            trace_html += f"[{step['agent']}] {step['action']} → <b>{step['status']}</b><br>"
        trace_html += "</div>"

        security_html = """
        <p style="background:#fff3cd;padding:10px;border-radius:5px;
                  font-size:13px;">
        🔒 Your prescription image was processed in-memory and deleted 
        immediately after analysis. No personal data is stored on our servers.
        </p>
        """

        download_html = f"""
        <a href="/download/{report_id}" 
           style="display:inline-block;background:#2c7a7b;color:white;
                  padding:10px 20px;border-radius:5px;text-decoration:none;
                  margin-bottom:20px;font-weight:bold;">
           📄 Download Report (PDF)
        </a>
        """

        html = f"""
        <html><head><title>MedBridge Results</title>
        <style>
            body {{ font-family: Arial; max-width: 700px; 
                   margin: 30px auto; padding: 20px; }}
            .card {{ background: #f0f9f9; border-left: 4px solid #2c7a7b;
                    padding: 15px; margin: 15px 0; border-radius: 5px; }}
            h2 {{ color: #2c7a7b; }}
            a {{ color: #2c7a7b; }}
        </style></head><body>
        <h1>🏥 MedBridge Results</h1>
        {security_html}
        {download_html}
        {trace_html}
        <p>Found <b>{result['total_medicines']} medicine(s)</b> 
           in your prescription</p>
        """

        for med in result["medicines"]:
            html += f"""
            <div class="card">
                <h2>💊 {med['medicine']}</h2>
                <p><b>Dosage:</b> {med['dosage']} | 
                   <b>Frequency:</b> {med['frequency']} | 
                   <b>Duration:</b> {med['duration']}</p>
                <h3>📖 What is this medicine?</h3>
                <p>{med['explanation']}</p>
                <h3>🗺️ Where to buy?</h3>
                <p>{med['pharmacy_info']}</p>
                <h3>⏰ Reminder</h3>
                <pre style="white-space:pre-wrap;">{med['reminder']}</pre>
            </div>
            """

        html += download_html  # also show button at bottom for convenience
        html += "<br><a href='/'>← Analyze another prescription</a>"
        html += "</body></html>"
        return html

    except Exception as e:
        return f"""
        <html><body style="font-family:Arial;max-width:600px;margin:50px auto;">
        <h2 style="color:#c0392b;">⚠️ Something went wrong</h2>
        <p>{str(e)}</p>
        <p>If this is a quota error, please wait a minute and try again, 
           or try with fewer medicines.</p>
        <a href="/">← Go back</a>
        </body></html>
        """

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
            content="Report not found or has expired. Please analyze your prescription again.",
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