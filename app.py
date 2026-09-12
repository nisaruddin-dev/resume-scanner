import json
import re

import google.generativeai as genai
import streamlit as st

import scanner

st.set_page_config(page_title="Resume Scanner", page_icon="📄", layout="wide")


@st.cache_data(ttl=3600, show_spinner=False)
def cached_extract(name: str, data: bytes) -> dict:
    return scanner.extract_text(name, data)


@st.cache_data(ttl=3600, show_spinner=False)
def cached_score(text: str, jd: str) -> dict:
    return scanner.compute_score(text, jd)


def call_gemini(resume: str, jd: str, breakdown: list, missing: list) -> dict | None:
    api_key = st.secrets.get("GEMINI_API_KEY", "")
    if not api_key:
        print("GEMINI ERROR: GEMINI_API_KEY missing from secrets.toml")
        return None

    genai.configure(api_key=api_key)

    prompt = f"""You are an expert resume reviewer.

A candidate uploaded their resume. A rule-based pre-scan produced the breakdown below.
Give honest, actionable feedback.

=== RESUME TEXT ===
{resume[:15000]}

=== RULE-BASED PRE-SCAN ===
{json.dumps(breakdown, indent=2)}

=== MISSING KEYWORDS (from job description) ===
{json.dumps(missing)}

=== JOB DESCRIPTION ===
{jd[:5000] if jd.strip() else "(none provided)"}

Respond with ONLY this JSON:
{{
  "overall_score": 0,
  "verdict": "Strong | Needs work | Weak",
  "summary": "1-2 sentence honest summary",
  "strengths": ["string", "string", "string"],
  "improvements": [
    {{"issue": "what's wrong", "fix": "how to fix", "impact": "High | Medium | Low"}}
  ],
  "missing_keywords": ["keyword1", "keyword2"],
  "rewrite_suggestions": [
    {{"original": "weak bullet", "improved": "stronger version"}}
  ]
}}

Rules:
- overall_score: integer 0-100. Most real resumes land 45-75.
- 3-5 strengths, 3-6 improvements (High impact first), 2-4 rewrites.
- Never invent facts — use "[X]%" placeholders if a metric is missing.
"""

    model = genai.GenerativeModel("gemini-3.6-flash")

    try:
        r = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"},
        )
        return json.loads(r.text)
    except Exception as e:
        print("GEMINI PRIMARY ERROR:", repr(e))
        try:
            r2 = model.generate_content(
                prompt,
                generation_config={"response_mime_type": "text/plain"},
            )
            raw = r2.text.strip()
            cleaned = re.sub(r"^```(?:json)?\s*", "", raw)
            cleaned = re.sub(r"\s*```$", "", cleaned)
            return json.loads(cleaned)
        except Exception as e2:
            print("GEMINI FALLBACK ERROR:", repr(e2))
            return None


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

st.title("📄 Resume Scanner")
st.caption("ATS-style quality score + honest improvement suggestions — powered by Gemini")

with st.sidebar:
    st.header("Upload")
    uploaded = st.file_uploader("Resume (PDF or DOCX)", type=["pdf", "docx"])
    st.divider()
    st.header("Optional")
    jd = st.text_area("Paste a job description",
                      height=200,
                      placeholder="Paste a JD here to score keyword match…")

if uploaded is None:
    st.info("👈 Upload a resume from the sidebar to get started.")
    st.stop()

data = uploaded.getvalue()
if len(data) > 5 * 1024 * 1024:
    st.error("File larger than 5 MB. Please upload a smaller resume.")
    st.stop()

with st.spinner("Extracting text…"):
    ext = cached_extract(uploaded.name, data)

if not ext["ok"]:
    st.error(f"Could not read the file: {ext['error']}")
    st.stop()

resume_text = ext["summary"]["text"]

with st.spinner("Computing rule-based score…"):
    sc = cached_score(resume_text, jd)

if not sc["ok"]:
    st.error(f"Scoring failed: {sc['error']}")
    st.stop()

s = sc["summary"]
breakdown = s["breakdown"]
missing = s.get("missing_keywords", [])

st.subheader("📊 Rule-based quality score")
c1, c2 = st.columns([1, 3])
with c1:
    st.metric("Score", f"{s['overall_score']}/100")
with c2:
    st.progress(s["overall_score"] / 100)

with st.expander("See per-category breakdown"):
    for row in breakdown:
        pct = (row["score"] / row["max"]) if row["max"] else 0.0
        st.markdown(f"**{row['name']}** — {row['score']}/{row['max']}")
        st.progress(pct)
        st.caption(row["notes"])

with st.spinner("Asking Gemini for feedback…"):
    ai = call_gemini(resume_text, jd, breakdown, missing)

if ai is None:
    st.warning("AI feedback unavailable — the rule-based score above is still valid.")
    st.stop()

st.divider()
st.subheader("🤖 AI feedback")

verdict = ai.get("verdict", "Unknown")
score = ai.get("overall_score", 0)

c1, c2 = st.columns([3, 1])
with c1:
    if verdict == "Strong":
        st.success(f"### {verdict} resume")
    elif verdict == "Needs work":
        st.warning(f"### {verdict}")
    else:
        st.error(f"### {verdict}")
with c2:
    st.metric("AI score", f"{score}/100")

st.write(ai.get("summary", ""))

colA, colB = st.columns(2)
with colA:
    st.markdown("#### ✅ Strengths")
    for x in ai.get("strengths", []):
        st.markdown(f"- {x}")
with colB:
    st.markdown("#### 🔧 Improvements")
    for imp in ai.get("improvements", []):
        impact = imp.get("impact", "Medium")
        emoji = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(impact, "⚪")
        st.markdown(f"{emoji} **{imp.get('issue', '')}**")
        st.caption(f"Fix: {imp.get('fix', '')}")

mk = ai.get("missing_keywords", [])
if mk:
    st.markdown("#### 🔑 Missing keywords")
    st.markdown(" ".join(f"`{k}`" for k in mk))

rw = ai.get("rewrite_suggestions", [])
if rw:
    st.markdown("#### ✍️ Rewrite suggestions")
    for item in rw:
        a, b = st.columns(2)
        with a:
            st.markdown("**Before**")
            st.info(item.get("original", ""))
        with b:
            st.markdown("**After**")
            st.success(item.get("improved", ""))

with st.expander("🔎 Extracted resume text (debug)"):
    st.text(resume_text[:3000] + ("…" if len(resume_text) > 3000 else ""))