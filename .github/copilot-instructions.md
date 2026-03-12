# AI Coding Agent Instructions - Job Apply Agent

## Project Overview

**Purpose**: A job scraping and resume optimization agent that searches LinkedIn, Seek, and Glassdoor, scores resume compatibility, and tailors resumes to maximize interview chances.

**Current Stage**: Prototype in progress. Indeed scraper (BeautifulSoup) implemented; LinkedIn/Seek/Glassdoor require Playwright. Resume matching and OpenAI-powered tailoring pending.

**Tech Stack**: Python 3, requests, BeautifulSoup4, Playwright (for dynamic sites), PyPDF2, scikit-learn (TF-IDF), OpenAI API, python-dotenv

## Entry Point & Architecture

- **Main Entry**: `src.main` module with CLI interface
- **Usage Pattern**: `python -m src.main --resume <pdf_path> --query <job_title> --location <city> --sources linkedin,seek,glassdoor --tailor`
- **Architecture Flow**:
  1. Parse resume (PDF → structured text)
  2. Scrape jobs from multiple sources (LinkedIn/Seek/Glassdoor/Indeed)
  3. Score & rank jobs by resume match
  4. Optionally tailor resume for top matches (OpenAI) to optimize for interview
- **Output**: Ranked job list with compatibility scores + (optional) tailored resume snippets

## Key Components to Build

1. **Resume Parser** (`src/resume_parser.py`): Extract text/structured data from PDF using PyPDF2
2. **Job Scrapers** (`src/job_scraper.py`):
   - `IndeedScraper`: BeautifulSoup-based (already implemented, uses requests)
   - `LinkedInScraper`, `SeekScraper`, `GlassdoorScraper`: Playwright-based (dynamic content; browser automation required)
   - All scrapers return standardized `JobPosting` objects
3. **Resume Matcher** (`src/resume_matcher.py`): Core matching logic using similarity scoring:
   - Extract and normalize skills/keywords from resume and job description
   - Use TF-IDF or cosine similarity (scikit-learn) to compute semantic overlap
   - Produce normalized score 0-100 with breakdown of matched skills/keywords
4. **Resume Tailor** (`src/resume_tailor.py`): OpenAI integration for optimization:
   - Highlight relevant skills/experience for top-matching jobs
   - Generate tailored cover letter snippets or resume sections
5. **Main CLI** (`src/main.py`): argparse interface binding all components; reads `.env` for OPENAI_API_KEY and USER_AGENT

## Environment & Configuration

- Copy `.env.example` to `.env` for local development
- **Required vars**: `OPENAI_API_KEY` (for future AI integration), `USER_AGENT` (for web scraping)
- No database or external service required yet; all processing is in-memory

## Dependencies & Development

- **Install**: `pip install -r requirements.txt`
- **Testing**: Not yet defined; recommend pytest structure under `tests/` when implementing
- **Playwright**: Required for LinkedIn/Seek/Glassdoor scrapers. Install: `playwright install` (sets up browser drivers)
- **Future scope**: Multi-threaded scraping for performance, caching layer to avoid re-scraping, resume version control

## Code Patterns to Follow

- Use environment variables via `python-dotenv` for all external config (API keys, user agents)
- Modularize scrapers - separate parser logic from HTTP client (enables testing, rotation strategies)
- **Resume matching strategy**: Extract noun phrases/keywords from both resume and job description, then compute similarity:
  - Normalize text (lowercase, strip punctuation, tokenize)
  - Calculate TF-IDF vectors or use simple keyword overlap with weighted scoring for high-value terms (e.g., programming languages, frameworks)
  - Return scored results with explainability - which skills/keywords matched and which didn't
- Resume matching should be deterministic and explainable (log which skills matched, weights used)
- CLI should fail gracefully with informative messages (missing PDF, network errors, parsing failures)

## Common Workflows

- **Run with test resume**: `python -m src.main --resume sample.pdf --query "python developer" --location "Sydney" --limit 5`
- **Debug parsing**: Test PyPDF2 extraction on resume before running full pipeline
- **Check scraper**: Verify Indeed HTML structure periodically (sites evolve; BeautifulSoup selectors may break)
- **Iterating resume matching**: Develop in isolation with mock job data before integrating full scraper
