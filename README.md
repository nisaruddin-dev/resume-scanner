# 📄 Resume Scanner

A Streamlit web app that scores a resume against common ATS (Applicant Tracking System) quality heuristics and gives honest, AI-powered improvement suggestions using Google Gemini.

Upload a PDF or DOCX, optionally paste a job description, and get:
- A **rule-based quality score** (0–100) with a per-category breakdown
- **AI feedback** with strengths, prioritized improvements, missing keywords, and concrete rewrite examples

🔗 **Live app:** https://resume-scanner-io.streamlit.app

---

## ✨ Features

- **Auto-extraction** from PDF (`pdfplumber`) and DOCX (`python-docx`)
- **Rule-based scoring** across 6 dimensions:
  - Contact info completeness (email, phone, LinkedIn)
  - Section headers (Experience, Education, Skills, Projects)
  - Quantified achievements (numbers, %, $ in bullets)
  - Strong action verbs starting bullets
  - Resume length (ideal: 400–900 words)
  - Formatting red flags (multi-column layouts, tables)
- **Job-description keyword match** (optional) — paste a JD and get a keyword-overlap score plus a list of missing keywords
- **Gemini 3.6 Flash analysis** — plain-English strengths, improvements, and rewrite examples
- **Graceful degradation** — if the AI call fails, the rule-based score still displays

---

## 🧠 How it actually works

There is **no universal "ATS score"** — every ATS platform uses its own algorithm, and most don't expose a number. This app computes a **resume quality score** based on well-established heuristics that correlate with good ATS performance. It's a heuristic, not an oracle.

The app has two layers:

1. **Rule-based scoring** (deterministic, in `scanner.py`) — fast, transparent, no AI needed.
2. **Gemini analysis** — turns the breakdown into personalized advice, examples, and rewrites.

If Gemini is unavailable, the rule-based score still shows. The app never depends on a single external service.

---

## 🚀 Run locally

```bash
git clone https://github.com/nisaruddin-dev/resume-scanner.git
cd resume-scanner
pip install -r requirements.txt
Create .streamlit/secrets.toml from the example:

bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
Add your Gemini API key:

toml
GEMINI_API_KEY = "your_gemini_api_key_here"
Get a free key at aistudio.google.com/apikey.

Run:

bash
python -m streamlit run app.py
Open http://localhost:8501.

📁 Project structure
text
resume-scanner/
├── app.py                       # Streamlit UI + Gemini call
├── scanner.py                   # Extraction + rule-based scoring
├── requirements.txt
├── README.md
└── .streamlit/
    └── secrets.toml.example     # Copy → secrets.toml (gitignored)
Architecture rule: scanner.py never imports Streamlit, and app.py never defines scoring logic. Adding a new scoring rule = one function in scanner.py + one line in SCORERS. Nothing else changes.

🛠️ Tech stack
Streamlit — UI

pdfplumber — PDF text extraction

python-docx — DOCX text extraction

Google Gemini 3.6 Flash — AI feedback via google-generativeai

📌 Notes & limitations
Image-only PDFs (scanned resumes) can't be parsed — you'll get a friendly error. Use a text-based PDF or DOCX.

File size limit: 5 MB.

Gemini free tier: ~15 requests/minute. Fine for personal use, may throttle under heavy traffic.

ATS scores are heuristic. Don't treat the number as gospel — read the per-category breakdown and the AI feedback.

📜 License
MIT — do whatever you want with it.

🙏 Acknowledgements
Built as a learning project. Feedback welcome via GitHub issues.
