"""Command-line interface for the job‑apply‑agent prototype.

This module ties together the resume parser and the various
scrapers (Indeed + Playwright-based) so that a user can run
a single command and get back a list of jobs matching their query.

Example:

    python -m src.main --resume my_resume.pdf \
        --query "python developer" --location Sydney \
        --sources indeed,linkedin,seek --limit 5

Playwright scrapers are asynchronous and require the `playwright`
package (run `playwright install` first).
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from typing import List, Set

from src.resume_parser import ResumeParser
from src.job_scraper import IndeedScraper, JobPosting as IndeedJob

# import async scrapers lazily so that the CLI can still be used without
# playwright installed if the user only requests `indeed`.
try:
    from src.job_scrapers_playwright import (
        LinkedInScraper,
        SeekScraper,
        GlassdoorScraper,
        JobPosting as PWJob,
    )
except ImportError:  # pragma: no cover - optional dependency
    LinkedInScraper = SeekScraper = GlassdoorScraper = None  # type: ignore


def score_job(job: IndeedJob | PWJob, resume_skills: list[str]) -> tuple[int, list[str]]:
    """Return (matched_count, matched_skills) between job description and resume skills."""
    import re
    desc_lower = (job.description or "").lower()
    matched = [s for s in resume_skills if re.search(r'\b' + re.escape(s) + r'\b', desc_lower)]
    return len(matched), matched


def print_jobs(source: str, jobs: List[IndeedJob | PWJob], resume_skills: list[str] | None = None) -> None:
    """Pretty-print a collection of job postings."""

    print(f"\n=== {source.upper()} ({len(jobs)} jobs) ===")
    for job in jobs:
        print(f"- {job.title} at {job.company} ({job.location})")
        print(f"  {job.url}")
        if resume_skills:
            count, matched = score_job(job, resume_skills)
            total = len(resume_skills)
            pct = round(count / total * 100) if total else 0
            print(f"  Match: {count}/{total} skills ({pct}%) — {', '.join(matched) if matched else 'none'}")


def run_async_scrapers(
    query: str, location: str, limit: int, sources: Set[str]
) -> dict[str, List[PWJob]]:
    """Execute Playwright-based scrapers and return results.

    The caller must supply only names from {'linkedin','seek','glassdoor'}.
    """

    async def _worker() -> dict[str, List[PWJob]]:
        results: dict[str, List[PWJob]] = {}

        if "linkedin" in sources:
            if LinkedInScraper is None:
                raise RuntimeError("Playwright scrapers not available (install playwright)")
            li = LinkedInScraper()
            results["linkedin"] = await li.search(query, location, limit)
            await li.close_browser()

        if "seek" in sources:
            sk = SeekScraper()
            results["seek"] = await sk.search(query, location, limit)
            await sk.close_browser()

        if "glassdoor" in sources:
            gd = GlassdoorScraper()
            results["glassdoor"] = await gd.search(query, location, limit)
            await gd.close_browser()

        return results

    return asyncio.run(_worker())


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Job Apply Agent CLI")

    parser.add_argument("--resume", help="Path to PDF resume (optional)")
    parser.add_argument("--query", required=True, help="Job search query")
    parser.add_argument("--location", required=True, help="Job location")
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of jobs to return per source",
    )
    parser.add_argument(
        "--sources",
        default="indeed",
        help="Comma-separated list of sources: indeed, linkedin, seek, glassdoor",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    sources = {s.strip().lower() for s in args.sources.split(",") if s.strip()}
    if not sources:
        print("No sources specified; use --sources to choose at least one.")
        sys.exit(1)

    # optional resume parsing
    resume_skills: list[str] = []
    if args.resume:
        try:
            text = ResumeParser.extract_text(args.resume)
            resume_skills = ResumeParser.extract_skills(text or "")
            print(f"Parsed resume, found {len(resume_skills)} skills: {resume_skills}\n")
        except Exception as exc:
            print(f"Failed to parse resume: {exc}\n")

    all_results: dict[str, List[IndeedJob | PWJob]] = {}

    # synchronous Indeed scraper
    if "indeed" in sources:
        indeed = IndeedScraper()
        jobs = indeed.search(args.query, args.location, args.limit)
        all_results["indeed"] = jobs

    # asynchronous Playwright scrapers
    async_sources = sources & {"linkedin", "seek", "glassdoor"}
    if async_sources:
        try:
            results = run_async_scrapers(args.query, args.location, args.limit, async_sources)
            all_results.update(results)
        except Exception as exc:
            print(f"Error running Playwright scrapers: {exc}")

    # print summary
    for source, jobs in all_results.items():
        print_jobs(source, jobs, resume_skills or None)


if __name__ == "__main__":
    main()
