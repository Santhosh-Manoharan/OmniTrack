"""
OmniTrack Receipt Upload Service
Simple web frontend + API for uploading receipt images.
"""
import os
import json
import tempfile
import requests
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse

app = FastAPI(title="OmniTrack Receipt Upload", version="1.0")

N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "http://n8n:5678/webhook/upload-receipt")
PAPERLESS_URL = os.getenv("PAPERLESS_URL", "http://paperless:8000")
PAPERLESS_TOKEN = os.getenv("PAPERLESS_TOKEN", "")

UPLOAD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>OmniTrack - Upload Receipt</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #e2e8f0; min-height: 100vh; display: flex; flex-direction: column; align-items: center; padding: 2rem; }
  h1 { color: #38bdf8; margin-bottom: 0.5rem; }
  .subtitle { color: #94a3b8; margin-bottom: 2rem; }
  .card { background: #1e293b; border-radius: 12px; padding: 2rem; width: 100%; max-width: 480px; border: 1px solid #334155; }
  .dropzone { border: 2px dashed #475569; border-radius: 8px; padding: 2rem; text-align: center; cursor: pointer; transition: all 0.2s; margin-bottom: 1rem; }
  .dropzone:hover, .dropzone.dragover { border-color: #38bdf8; background: #1e3a5f; }
  .dropzone input { display: none; }
  .preview { max-width: 100%; max-height: 300px; border-radius: 8px; margin: 1rem 0; display: none; }
  button { width: 100%; padding: 0.75rem; background: #0ea5e9; color: white; border: none; border-radius: 8px; font-size: 1rem; cursor: pointer; transition: background 0.2s; }
  button:hover { background: #0284c7; }
  button:disabled { background: #475569; cursor: not-allowed; }
  .result { margin-top: 1rem; padding: 1rem; border-radius: 8px; display: none; }
  .result.success { background: #166534; border: 1px solid #22c55e; }
  .result.error { background: #7f1d1d; border: 1px solid #ef4444; }
  .loading { display: none; text-align: center; color: #94a3b8; }
</style>
</head>
<body>
<h1>📄 OmniTrack</h1>
<p class="subtitle">Upload a receipt to track your expense</p>
<div class="card">
  <div class="dropzone" id="dropzone">
    <p>📷 Tap or drag receipt image here</p>
    <input type="file" id="fileInput" accept="image/*">
  </div>
  <img id="preview" class="preview">
  <button id="uploadBtn" disabled>Upload Receipt</button>
  <div class="loading" id="loading">⏳ Processing with AI...</div>
  <div class="result" id="result"></div>
</div>
<script>
const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('fileInput');
const preview = document.getElementById('preview');
const uploadBtn = document.getElementById('uploadBtn');
const loading = document.getElementById('loading');
const result = document.getElementById('result');
let selectedFile = null;

dropzone.addEventListener('click', () => fileInput.click());
dropzone.addEventListener('dragover', (e) => { e.preventDefault(); dropzone.classList.add('dragover'); });
dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));
dropzone.addEventListener('drop', (e) => { e.preventDefault(); dropzone.classList.remove('dragover'); if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]); });
fileInput.addEventListener('change', (e) => { if (e.target.files[0]) handleFile(e.target.files[0]); });

function handleFile(file) {
  selectedFile = file;
  const reader = new FileReader();
  reader.onload = (e) => { preview.src = e.target.result; preview.style.display = 'block'; uploadBtn.disabled = false; };
  reader.readAsDataURL(file);
}

uploadBtn.addEventListener('click', async () => {
  if (!selectedFile) return;
  const formData = new FormData();
  formData.append('file', selectedFile);
  uploadBtn.disabled = true;
  loading.style.display = 'block';
  result.style.display = 'none';
  try {
    const resp = await fetch('/upload', { method: 'POST', body: formData });
    const data = await resp.json();
    loading.style.display = 'none';
    result.style.display = 'block';
    if (data.success) {
      result.className = 'result success';
      result.innerHTML = `<strong>✅ Receipt processed!</strong><br>Vendor: ${data.vendor || 'Unknown'}<br>Amount: ₹${data.total || '?'}<br>Category: ${data.category || 'other'}`;
    } else {
      result.className = 'result error';
      result.innerHTML = `<strong>❌ Error:</strong> ${data.error || 'Unknown error'}`;
    }
  } catch (e) {
    loading.style.display = 'none';
    result.style.display = 'block';
    result.className = 'result error';
    result.innerHTML = `<strong>❌ Error:</strong> ${e.message}`;
  }
  uploadBtn.disabled = false;
});
</script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def index():
    return UPLOAD_HTML


@app.post("/upload")
async def upload_receipt(file: UploadFile = File(...)):
    """Upload receipt image, forward to n8n webhook for processing."""
    # Save uploaded file temporarily
    suffix = os.path.splitext(file.filename or "receipt.jpg")[1] or ".jpg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # Forward to n8n webhook
        with open(tmp_path, "rb") as f:
            files = {"file": (file.filename or "receipt.jpg", f, file.content_type or "image/jpeg")}
            resp = requests.post(N8N_WEBHOOK_URL, files=files, timeout=120)

        if resp.status_code == 200:
            return resp.json()
        else:
            raise HTTPException(status_code=500, detail=f"n8n returned {resp.status_code}: {resp.text[:200]}")
    except requests.exceptions.ConnectionError:
        raise HTTPException(status_code=503, detail="Cannot connect to n8n webhook")
    finally:
        os.unlink(tmp_path)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "receipt-upload"}
