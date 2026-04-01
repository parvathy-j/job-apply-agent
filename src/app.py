"""Streamlit UI for the job-apply-agent prototype."""

from __future__ import annotations

import asyncio
import sys
import os
import tempfile
from typing import List

# Ensure the project root is on sys.path so `src.*` imports resolve
# regardless of how streamlit was invoked.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st

from src.resume_parser import ResumeParser
from src.job_scraper import IndeedScraper, JobPosting as IndeedJob
from src.main import score_job, run_async_scrapers

try:
    from src.job_scrapers_playwright import JobPosting as PWJob
except ImportError:
    PWJob = IndeedJob  # type: ignore


st.set_page_config(page_title="Job Apply Agent", page_icon="💼", layout="wide")
st.title("💼 Job Apply Agent")

# ── Sidebar inputs ────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Search settings")

    query = st.text_input("Job query", placeholder="e.g. python developer")
    location = st.text_input("Location", placeholder="e.g. Sydney")
    limit = st.slider("Max jobs per source", 1, 50, 10)

    st.subheader("Sources")
    use_indeed = st.checkbox("Indeed", value=True)
    use_linkedin = st.checkbox("LinkedIn (requires Playwright)")
    use_seek = st.checkbox("Seek (requires Playwright)")
    use_glassdoor = st.checkbox("Glassdoor (requires Playwright)")

    st.subheader("Resume (optional)")
    uploaded_resume = st.file_uploader("Upload PDF resume", type=["pdf"])

    search_btn = st.button("Search", type="primary", use_container_width=True)

# ── Main area ─────────────────────────────────────────────────────────────────
if not search_btn:
    st.info("Configure your search in the sidebar and click **Search**.")
    st.stop()

if not query or not location:
    st.error("Please enter both a job query and a location.")
    st.stop()

sources = set()
if use_indeed:
    sources.add("indeed")
if use_linkedin:
    sources.add("linkedin")
if use_seek:
    sources.add("seek")
if use_glassdoor:
    sources.add("glassdoor")

if not sources:
    st.error("Select at least one source.")
    st.stop()

# Parse resume
resume_skills: list[str] = []
if uploaded_resume:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_resume.read())
        tmp_path = tmp.name
    try:
        text = ResumeParser.extract_text(tmp_path)
        resume_skills = ResumeParser.extract_skills(text or "")
        st.success(f"Resume parsed — {len(resume_skills)} skills found: {', '.join(sorted(resume_skills))}")
    except Exception as exc:
        st.warning(f"Could not parse resume: {exc}")
    finally:
        os.unlink(tmp_path)

# Run scrapers
all_results: dict[str, list] = {}

with st.spinner("Searching jobs…"):
    if "indeed" in sources:
        try:
            scraper = IndeedScraper()
            all_results["indeed"] = scraper.search(query, location, limit)
        except Exception as exc:
            st.warning(f"Indeed scraper error: {exc}")

    async_sources = sources & {"linkedin", "seek", "glassdoor"}
    if async_sources:
        try:
            results = run_async_scrapers(query, location, limit, async_sources)
            all_results.update(results)
        except Exception as exc:
            st.warning(f"Playwright scraper error: {exc}")

# Display results
total_jobs = sum(len(jobs) for jobs in all_results.values())
if total_jobs == 0:
    st.warning("No jobs found. Try a different query or location.")
    st.stop()

st.subheader(f"Results — {total_jobs} job(s) across {len(all_results)} source(s)")

for source, jobs in all_results.items():
    with st.expander(f"{source.upper()} — {len(jobs)} job(s)", expanded=True):
        for job in jobs:
            col1, col2 = st.columns([3, 1])

            with col1:
                st.markdown(f"**[{job.title}]({job.url})**")
                st.caption(f"{job.company} · {job.location}" + (f" · {job.salary}" if job.salary else ""))
                if job.description:
                    st.write(job.description[:300] + ("…" if len(job.description) > 300 else ""))

            with col2:
                if resume_skills:
                    count, matched = score_job(job, resume_skills)
                    total = len(resume_skills)
                    pct = round(count / total * 100) if total else 0
                    st.metric("Match", f"{pct}%", f"{count}/{total} skills")
                    if matched:
                        st.caption(", ".join(matched))

            st.divider()
