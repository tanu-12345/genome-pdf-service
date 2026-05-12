# Deploy Genome PDF Service on Railway

## Steps (10 minutes)

1. Create free account at railway.app
2. New Project → Deploy from GitHub (or use Railway CLI)
3. Upload these 4 files:
   - genome_pdf_service.py
   - genome_logo_clean.png   ← the cleaned logo
   - requirements_pdf_service.txt
   - Procfile

4. Railway auto-detects Python, installs deps, deploys.
5. Copy your Railway URL (e.g. https://genome-pdf.up.railway.app)
6. In n8n → Variables → Add: PDF_SERVICE_URL = https://genome-pdf.up.railway.app/generate

## Test it
curl -X POST https://your-url.railway.app/generate \
  -H "Content-Type: application/json" \
  -d '{"site_id":"TEST-01","client_name":"Test Client","status":"On Track","progress_pct":75,"work_phase":"Foundation","supervisor_name":"Test Supervisor","raw_text":"Test work done","blockers":"None","next_steps":"Continue tomorrow","report_date":"12 May 2026"}' \
  --output test_report.pdf

## Security (add after confirming it works)
Add API key check in Flask:
  SECRET = os.environ.get('PDF_SECRET_KEY')
  if request.headers.get('X-API-Key') != SECRET: return 403
Then set PDF_SECRET_KEY in Railway env + n8n Variables.
