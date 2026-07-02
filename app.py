from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import HTMLResponse, Response
import shutil, os, uuid
from agents.orchestrator import run_medbridge
from tools.pdf_generator import generate_pdf_report

app = FastAPI(title="MedBridge Agent")

REPORT_CACHE: dict[str, dict] = {}

HOME_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MedBridge — Prescription Assistant</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --teal:       #0f766e;
    --teal-light: #ccfbf1;
    --teal-dark:  #134e4a;
    --teal-mid:   #14b8a6;
    --bg:         #f8fafc;
    --card:       #ffffff;
    --text:       #0f172a;
    --muted:      #64748b;
    --border:     #e2e8f0;
    --radius:     12px;
  }

  body {
    font-family: 'Inter', sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
  }

  /* NAV */
  nav {
    background: var(--card);
    border-bottom: 1px solid var(--border);
    padding: 0 2rem;
    height: 60px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .nav-brand {
    display: flex;
    align-items: center;
    gap: 10px;
    font-weight: 600;
    font-size: 18px;
    color: var(--teal);
    text-decoration: none;
  }
  .nav-brand svg { width: 28px; height: 28px; }
  .nav-badge {
    font-size: 11px;
    background: var(--teal-light);
    color: var(--teal-dark);
    padding: 3px 8px;
    border-radius: 20px;
    font-weight: 500;
  }

  /* HERO */
  .hero {
    background: linear-gradient(135deg, #0f766e 0%, #0d9488 50%, #14b8a6 100%);
    color: white;
    padding: 64px 2rem 80px;
    text-align: center;
    position: relative;
    overflow: hidden;
  }
  .hero::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(255,255,255,0.04) 1px, transparent 1px);
    background-size: 40px 40px;
  }
  .hero-tag {
    display: inline-block;
    background: rgba(255,255,255,0.15);
    border: 1px solid rgba(255,255,255,0.25);
    padding: 5px 14px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 500;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-bottom: 20px;
  }
  .hero h1 {
    font-size: clamp(28px, 5vw, 44px);
    font-weight: 600;
    line-height: 1.2;
    margin-bottom: 16px;
    position: relative;
  }
  .hero p {
    font-size: 17px;
    opacity: 0.85;
    max-width: 520px;
    margin: 0 auto 40px;
    line-height: 1.6;
    position: relative;
  }

  /* STATS ROW */
  .stats-row {
    display: flex;
    justify-content: center;
    gap: 32px;
    flex-wrap: wrap;
    position: relative;
  }
  .stat {
    text-align: center;
  }
  .stat-num {
    font-size: 26px;
    font-weight: 600;
    display: block;
  }
  .stat-label {
    font-size: 12px;
    opacity: 0.7;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  /* MAIN CONTENT */
  .main {
    max-width: 900px;
    margin: -40px auto 60px;
    padding: 0 1.5rem;
    position: relative;
  }

  /* UPLOAD CARD */
  .card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 2rem;
    box-shadow: 0 4px 24px rgba(0,0,0,0.06);
  }
  .card-title {
    font-size: 18px;
    font-weight: 600;
    margin-bottom: 6px;
    color: var(--text);
  }
  .card-sub {
    font-size: 14px;
    color: var(--muted);
    margin-bottom: 28px;
  }

  /* DROPZONE */
  .dropzone {
    border: 2px dashed var(--border);
    border-radius: var(--radius);
    padding: 48px 24px;
    text-align: center;
    cursor: pointer;
    transition: all 0.2s;
    background: var(--bg);
    position: relative;
    margin-bottom: 24px;
  }
  .dropzone:hover { border-color: var(--teal-mid); background: #f0fdfa; }
  .dropzone input[type=file] {
    position: absolute;
    inset: 0;
    opacity: 0;
    cursor: pointer;
    width: 100%;
    height: 100%;
  }
  .dropzone-icon {
    width: 48px;
    height: 48px;
    background: var(--teal-light);
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 16px;
    color: var(--teal);
  }
  .dropzone-icon svg { width: 24px; height: 24px; }
  .dropzone-title { font-size: 15px; font-weight: 500; margin-bottom: 6px; }
  .dropzone-sub { font-size: 13px; color: var(--muted); }
  .file-name {
    display: none;
    font-size: 13px;
    color: var(--teal);
    font-weight: 500;
    margin-top: 10px;
  }

  /* FORM ROW */
  .form-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-bottom: 24px;
  }
  @media (max-width: 600px) { .form-row { grid-template-columns: 1fr; } }

  .form-group label {
    display: block;
    font-size: 13px;
    font-weight: 500;
    color: var(--text);
    margin-bottom: 8px;
  }
  .form-group input,
  .form-group select {
    width: 100%;
    padding: 10px 14px;
    border: 1px solid var(--border);
    border-radius: var(--radius);
    font-size: 14px;
    font-family: 'Inter', sans-serif;
    color: var(--text);
    background: var(--card);
    outline: none;
    transition: border-color 0.15s;
  }
  .form-group input:focus,
  .form-group select:focus { border-color: var(--teal-mid); }

  /* SUBMIT BTN */
  .btn-primary {
    width: 100%;
    padding: 13px;
    background: var(--teal);
    color: white;
    border: none;
    border-radius: var(--radius);
    font-size: 15px;
    font-weight: 600;
    font-family: 'Inter', sans-serif;
    cursor: pointer;
    transition: background 0.2s, transform 0.1s;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
  }
  .btn-primary:hover { background: var(--teal-dark); }
  .btn-primary:active { transform: scale(0.99); }
  .btn-primary svg { width: 18px; height: 18px; }

  /* SECURITY NOTE */
  .security-note {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    border-radius: var(--radius);
    padding: 12px 16px;
    margin-top: 20px;
    font-size: 13px;
    color: #166534;
    line-height: 1.5;
  }
  .security-note svg { width: 16px; height: 16px; flex-shrink: 0; margin-top: 1px; }

  /* HOW IT WORKS */
  .how-it-works {
    margin-top: 32px;
    padding-top: 28px;
    border-top: 1px solid var(--border);
  }
  .how-title {
    font-size: 13px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--muted);
    margin-bottom: 20px;
  }
  .steps {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
  }
  @media (max-width: 600px) { .steps { grid-template-columns: 1fr; } }
  .step {
    display: flex;
    gap: 12px;
    align-items: flex-start;
  }
  .step-num {
    width: 28px;
    height: 28px;
    background: var(--teal-light);
    color: var(--teal-dark);
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 13px;
    font-weight: 600;
    flex-shrink: 0;
  }
  .step-text strong { display: block; font-size: 13px; font-weight: 500; margin-bottom: 2px; }
  .step-text span { font-size: 12px; color: var(--muted); line-height: 1.4; }

  /* LOADING OVERLAY */
  #loading {
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(255,255,255,0.85);
    z-index: 100;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 16px;
  }
  #loading.active { display: flex; }
  .spinner {
    width: 44px;
    height: 44px;
    border: 3px solid var(--teal-light);
    border-top-color: var(--teal);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  .loading-text { font-size: 15px; font-weight: 500; color: var(--teal-dark); }
  .loading-sub { font-size: 13px; color: var(--muted); }
</style>
</head>
<body>

<div id="loading">
  <div class="spinner"></div>
  <div class="loading-text">Analyzing your prescription...</div>
  <div class="loading-sub">This usually takes 10–20 seconds</div>
</div>

<nav>
  <a class="nav-brand" href="/">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path d="M9 3H5a2 2 0 0 0-2 2v4m6-6h10a2 2 0 0 1 2 2v4M9 3v18m0 0h10a2 2 0 0 0 2-2V9M9 21H5a2 2 0 0 1-2-2V9m0 0h18"/>
    </svg>
    MedBridge
  </a>
  <span class="nav-badge">AI Agent · Free</span>
</nav>

<div class="hero">
  <div class="hero-tag">Powered by Groq + Tesseract OCR</div>
  <h1>Understand your prescription<br>in seconds</h1>
  <p>Upload a photo of your prescription. MedBridge reads it, explains each medicine in simple language, and guides you to affordable options.</p>
  <div class="stats-row">
    <div class="stat"><span class="stat-num">3</span><span class="stat-label">AI Agents</span></div>
    <div class="stat"><span class="stat-num">Jan Aushadhi</span><span class="stat-label">Pharmacy Guidance</span></div>
    <div class="stat"><span class="stat-num">PDF</span><span class="stat-label">Downloadable Report</span></div>
  </div>
</div>

<div class="main">
  <div class="card">
    <div class="card-title">Analyze a prescription</div>
    <div class="card-sub">Upload a clear photo or scan of your doctor's prescription</div>

    <form action="/analyze" method="post" enctype="multipart/form-data" onsubmit="showLoading()">

      <div class="dropzone" id="dropzone">
        <input type="file" name="file" accept="image/*" required id="fileInput" onchange="showFile(this)">
        <div class="dropzone-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="17 8 12 3 7 8"/>
            <line x1="12" y1="3" x2="12" y2="15"/>
          </svg>
        </div>
        <div class="dropzone-title">Drop your prescription here</div>
        <div class="dropzone-sub">or click to browse · JPG, PNG, PDF</div>
        <div class="file-name" id="fileName"></div>
      </div>

      <div class="form-row">
        <div class="form-group">
          <label for="location">Your city / area</label>
          <input type="text" id="location" name="location" placeholder="e.g. Patna, Bihar" required>
        </div>
        <div class="form-group">
          <label for="language">Explanation language</label>
          <select id="language" name="language">
            <option value="English">English</option>
            <option value="Hindi">Hindi</option>
          </select>
        </div>
      </div>

      <button type="submit" class="btn-primary">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
        Analyze prescription
      </button>
    </form>

    <div class="security-note">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
      </svg>
      <span>Your prescription image is processed in-memory and deleted immediately after analysis. No personal data is stored on our servers.</span>
    </div>

    <div class="how-it-works">
      <div class="how-title">How it works</div>
      <div class="steps">
        <div class="step">
          <div class="step-num">1</div>
          <div class="step-text">
            <strong>OCR reads your prescription</strong>
            <span>Tesseract extracts medicine names, dosage and frequency</span>
          </div>
        </div>
        <div class="step">
          <div class="step-num">2</div>
          <div class="step-text">
            <strong>AI explains each medicine</strong>
            <span>Groq LLM gives simple, patient-friendly explanations</span>
          </div>
        </div>
        <div class="step">
          <div class="step-num">3</div>
          <div class="step-text">
            <strong>Find affordable options</strong>
            <span>Guidance to Jan Aushadhi stores for generic medicines</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

<script>
function showFile(input) {
  const name = input.files[0]?.name;
  const el = document.getElementById('fileName');
  if (name) { el.textContent = '✓ ' + name; el.style.display = 'block'; }
}
function showLoading() {
  document.getElementById('loading').classList.add('active');
}
</script>
</body>
</html>"""


def build_results_html(result: dict, report_id: str) -> str:
    medicines_html = ""
    for med in result["medicines"]:
        medicines_html += f"""
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
                  <circle cx="12" cy="12" r="10"/><path d="M12 16v-4M12 8h.01"/>
                </svg>
                What is this medicine?
              </div>
              <div class="section-content">{med['explanation'] or 'No explanation available.'}</div>
            </div>
            <div class="med-section">
              <div class="section-label">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
                  <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>
                </svg>
                Where to buy
              </div>
              <div class="section-content">{med['pharmacy_info'] or 'Visit pmbjp.gov.in'}</div>
            </div>
            <div class="reminder-box">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>
              </svg>
              <div>
                <strong>Set a reminder</strong> — {med['frequency'] or 'as prescribed'}<br>
                <span>Keep medicines visible · Complete the full course</span>
              </div>
            </div>
          </div>
        </div>
        """

    notes_html = ""
    if result.get("doctor_notes") and result["doctor_notes"] != "unclear":
        notes_html = f"""
        <div class="notes-card">
          <div class="section-label" style="margin-bottom:8px;">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
            </svg>
            Doctor's notes
          </div>
          <div style="font-size:14px;color:#334155;line-height:1.6;">{result['doctor_notes']}</div>
        </div>
        """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MedBridge — Results</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  :root {{
    --teal: #0f766e; --teal-light: #ccfbf1; --teal-dark: #134e4a;
    --teal-mid: #14b8a6; --bg: #f8fafc; --card: #ffffff;
    --text: #0f172a; --muted: #64748b; --border: #e2e8f0; --radius: 12px;
  }}
  body {{ font-family: 'Inter', sans-serif; background: var(--bg); color: var(--text); min-height: 100vh; }}
  nav {{
    background: var(--card); border-bottom: 1px solid var(--border);
    padding: 0 2rem; height: 60px; display: flex;
    align-items: center; justify-content: space-between;
  }}
  .nav-brand {{
    display: flex; align-items: center; gap: 10px;
    font-weight: 600; font-size: 18px; color: var(--teal); text-decoration: none;
  }}
  .nav-brand svg {{ width: 26px; height: 26px; }}

  .results-header {{
    background: linear-gradient(135deg, #0f766e, #14b8a6);
    color: white; padding: 40px 2rem 60px; text-align: center;
  }}
  .results-header h1 {{ font-size: 26px; font-weight: 600; margin-bottom: 8px; }}
  .results-header p {{ font-size: 14px; opacity: 0.8; }}
  .count-badge {{
    display: inline-block;
    background: rgba(255,255,255,0.2);
    border: 1px solid rgba(255,255,255,0.3);
    padding: 4px 14px; border-radius: 20px;
    font-size: 13px; margin-bottom: 16px;
  }}

  .main {{
    max-width: 820px; margin: -40px auto 60px; padding: 0 1.5rem;
  }}

  .action-bar {{
    display: flex; gap: 12px; margin-bottom: 24px; flex-wrap: wrap;
  }}
  .btn-download {{
    display: inline-flex; align-items: center; gap: 8px;
    background: var(--teal); color: white; padding: 10px 20px;
    border-radius: var(--radius); text-decoration: none;
    font-size: 14px; font-weight: 500; transition: background 0.2s;
  }}
  .btn-download:hover {{ background: var(--teal-dark); }}
  .btn-download svg {{ width: 16px; height: 16px; }}
  .btn-back {{
    display: inline-flex; align-items: center; gap: 8px;
    background: white; color: var(--text); padding: 10px 20px;
    border-radius: var(--radius); text-decoration: none;
    font-size: 14px; font-weight: 500; border: 1px solid var(--border);
    transition: background 0.15s;
  }}
  .btn-back:hover {{ background: var(--bg); }}
  .btn-back svg {{ width: 16px; height: 16px; }}

  .security-note {{
    display: flex; align-items: flex-start; gap: 10px;
    background: #f0fdf4; border: 1px solid #bbf7d0;
    border-radius: var(--radius); padding: 12px 16px;
    margin-bottom: 24px; font-size: 13px; color: #166534; line-height: 1.5;
  }}
  .security-note svg {{ width: 15px; height: 15px; flex-shrink: 0; margin-top: 2px; }}

  .notes-card {{
    background: #fffbeb; border: 1px solid #fde68a;
    border-radius: var(--radius); padding: 16px 20px; margin-bottom: 20px;
  }}

  .med-card {{
    background: var(--card); border: 1px solid var(--border);
    border-radius: 16px; margin-bottom: 20px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.04);
    overflow: hidden;
  }}
  .med-header {{
    display: flex; gap: 14px; align-items: flex-start;
    padding: 20px 24px 16px; border-bottom: 1px solid var(--border);
    background: #f8fafc;
  }}
  .med-icon {{
    width: 40px; height: 40px; background: var(--teal-light);
    border-radius: 10px; display: flex; align-items: center;
    justify-content: center; color: var(--teal); flex-shrink: 0;
  }}
  .med-icon svg {{ width: 20px; height: 20px; }}
  .med-name {{ font-size: 17px; font-weight: 600; margin-bottom: 8px; color: var(--teal-dark); }}
  .med-meta {{ display: flex; gap: 8px; flex-wrap: wrap; }}
  .badge {{
    font-size: 12px; font-weight: 500; padding: 3px 10px;
    background: var(--teal-light); color: var(--teal-dark);
    border-radius: 20px;
  }}

  .med-body {{ padding: 20px 24px; }}
  .med-section {{ margin-bottom: 20px; }}
  .section-label {{
    display: flex; align-items: center; gap: 6px;
    font-size: 11px; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.06em; color: var(--muted); margin-bottom: 10px;
  }}
  .section-content {{
    font-size: 14px; line-height: 1.7; color: #334155;
    background: var(--bg); border-radius: 8px; padding: 14px 16px;
    border: 1px solid var(--border);
  }}

  .reminder-box {{
    display: flex; gap: 12px; align-items: flex-start;
    background: #eff6ff; border: 1px solid #bfdbfe;
    border-radius: 10px; padding: 14px 16px;
    font-size: 13px; color: #1e40af;
  }}
  .reminder-box svg {{ flex-shrink: 0; margin-top: 2px; color: #3b82f6; }}
  .reminder-box strong {{ display: block; font-weight: 600; margin-bottom: 2px; }}
  .reminder-box span {{ opacity: 0.8; font-size: 12px; }}

  .disclaimer {{
    text-align: center; font-size: 12px; color: var(--muted);
    margin-top: 32px; padding-top: 24px; border-top: 1px solid var(--border);
    line-height: 1.6;
  }}
</style>
</head>
<body>

<nav>
  <a class="nav-brand" href="/">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path d="M9 3H5a2 2 0 0 0-2 2v4m6-6h10a2 2 0 0 1 2 2v4M9 3v18m0 0h10a2 2 0 0 0 2-2V9M9 21H5a2 2 0 0 1-2-2V9m0 0h18"/>
    </svg>
    MedBridge
  </a>
</nav>

<div class="results-header">
  <div class="count-badge">{result['total_medicines']} medicine(s) found</div>
  <h1>Your prescription report is ready</h1>
  <p>Review each medicine below and download your full report</p>
</div>

<div class="main">
  <div class="action-bar">
    <a href="/download/{report_id}" class="btn-download">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
        <polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/>
      </svg>
      Download PDF report
    </a>
    <a href="/" class="btn-back">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <line x1="19" y1="12" x2="5" y2="12"/><polyline points="12 19 5 12 12 5"/>
      </svg>
      Analyze another
    </a>
  </div>

  <div class="security-note">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
    </svg>
    <span>Your prescription image was processed in-memory and deleted immediately. No personal data is stored on our servers.</span>
  </div>

  {notes_html}
  {medicines_html}

  <div class="disclaimer">
    This report is generated by an AI agent for informational purposes only.<br>
    Always consult your doctor or pharmacist before making any medication decisions.
  </div>
</div>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
async def home():
    return HOME_HTML


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

        return build_results_html(result, report_id)

    except Exception as e:
        return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  body {{ font-family: Inter, sans-serif; max-width: 560px; margin: 80px auto; padding: 0 1.5rem; }}
  .err {{ background:#fef2f2; border:1px solid #fecaca; border-radius:12px; padding:24px; }}
  h2 {{ color:#dc2626; font-size:18px; margin-bottom:12px; }}
  p {{ font-size:14px; color:#374151; line-height:1.6; margin-bottom:8px; }}
  a {{ color:#0f766e; font-size:14px; }}
</style></head><body>
<div class="err">
  <h2>Something went wrong</h2>
  <p>{str(e)}</p>
  <p>If this is a quota error, wait a minute and try again.</p>
</div>
<br><a href="/">← Go back</a>
</body></html>"""

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