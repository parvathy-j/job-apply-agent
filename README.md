Job Apply Agent — local prototype

Quick scaffold for a job-scraping and resume-matching agent. This prototype accepts a PDF resume, searches Indeed, and scores matches.

Usage (from project root):

```bash
cd job-apply-agent
# simple Indeed search
python -m src.main --query "software engineer" --location "Sydney"

# include a resume and limit number of results per source
python -m src.main --resume /path/to/resume.pdf \
    --query "software engineer" --location "Sydney" --limit 10

# choose sources (comma-separated). Playwright scrapers require `playwright install`
python -m src.main --query "python developer" --location "Sydney" \
    --sources indeed,linkedin,seek --limit 5
```

Requirements: see `requirements.txt`.

What's next: add Playwright-based scrapers for LinkedIn/Glassdoor/Seek and an OpenAI integration for tailoring.
