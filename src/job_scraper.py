"""Indeed job scraper module with modular HTTP client and parser."""

import os
from typing import Optional
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup


@dataclass
class JobPosting:
    """Represents a single job posting."""
    title: str
    company: str
    location: str
    description: str
    url: str
    salary: Optional[str] = None


class IndeedClient:
    """HTTP client for fetching Indeed pages with user-agent rotation."""

    def __init__(self, user_agent: Optional[str] = None):
        """
        Initialize the Indeed client.
        
        Args:
            user_agent: Optional custom user-agent string. Falls back to env var USER_AGENT.
        """
        self.user_agent = user_agent or os.getenv("USER_AGENT", 
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent})

    def fetch_search_page(self, query: str, location: str, start: int = 0) -> Optional[str]:
        """
        Fetch a search results page from Indeed.
        
        Args:
            query: Job search query (e.g., "python developer")
            location: Job location (e.g., "Sydney")
            start: Result offset for pagination
            
        Returns:
            HTML content as string, or None if request fails.
        """
        url = "https://au.indeed.com/jobs"
        params = {
            "q": query,
            "l": location,
            "start": start,
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching Indeed page: {e}")
            return None

    def fetch_job_detail(self, job_url: str) -> Optional[str]:
        """
        Fetch full job description from Indeed job posting.
        
        Args:
            job_url: URL to the job posting
            
        Returns:
            HTML content as string, or None if request fails.
        """
        try:
            response = self.session.get(job_url, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching job detail: {e}")
            return None


class IndeedParser:
    """Parser for extracting job data from Indeed HTML."""

    @staticmethod
    def parse_search_results(html: str) -> list[JobPosting]:
        """
        Extract job listings from Indeed search results page.
        
        Args:
            html: HTML content of search results page
            
        Returns:
            List of JobPosting objects
        """
        soup = BeautifulSoup(html, "html.parser")
        jobs = []
        
        # Find all job result containers (adjust selector if Indeed HTML changes)
        job_cards = soup.find_all("div", class_="job_seen_beacon")
        
        for card in job_cards:
            try:
                # Extract job title and link
                title_elem = card.find("h2", class_="jobTitle")
                if not title_elem:
                    continue
                    
                title_link = title_elem.find("a")
                if not title_link:
                    continue
                    
                title = title_link.get_text(strip=True)
                job_url = title_link.get("href", "")
                if job_url and not job_url.startswith("http"):
                    job_url = "https://au.indeed.com" + job_url
                
                # Extract company
                company_elem = card.find("span", class_="companyName")
                company = company_elem.get_text(strip=True) if company_elem else "Unknown"
                
                # Extract location
                location_elem = card.find("div", class_="companyLocation")
                location = location_elem.get_text(strip=True) if location_elem else "Unknown"
                
                # Extract snippet/summary (not full description)
                snippet_elem = card.find("div", class_="job-snippet")
                description = snippet_elem.get_text(strip=True) if snippet_elem else ""
                
                # Extract salary if available
                salary_elem = card.find("div", class_="salary-snippet")
                salary = salary_elem.get_text(strip=True) if salary_elem else None
                
                job = JobPosting(
                    title=title,
                    company=company,
                    location=location,
                    description=description,
                    url=job_url,
                    salary=salary,
                )
                jobs.append(job)
                
            except Exception as e:
                print(f"Error parsing job card: {e}")
                continue
        
        return jobs

    @staticmethod
    def parse_job_detail(html: str) -> Optional[str]:
        """
        Extract full job description from Indeed job posting page.
        
        Args:
            html: HTML content of job posting page
            
        Returns:
            Full job description text, or None if not found.
        """
        soup = BeautifulSoup(html, "html.parser")
        
        # Find job description container (adjust selector if Indeed HTML changes)
        description_elem = soup.find("div", class_="jobsearch-jobDescriptionText")
        
        if description_elem:
            return description_elem.get_text(separator=" ", strip=True)
        
        return None


class IndeedScraper:
    """High-level scraper combining client and parser."""

    def __init__(self, user_agent: Optional[str] = None):
        """Initialize scraper with HTTP client and parser."""
        self.client = IndeedClient(user_agent)
        self.parser = IndeedParser()

    def search(self, query: str, location: str, limit: int = 10) -> list[JobPosting]:
        """
        Search Indeed for jobs and return postings.
        
        Args:
            query: Job search query
            location: Job location
            limit: Maximum number of jobs to retrieve
            
        Returns:
            List of JobPosting objects
        """
        all_jobs = []
        page = 0
        
        while len(all_jobs) < limit:
            start = page * 10  # Indeed uses 10 results per page
            html = self.client.fetch_search_page(query, location, start=start)
            
            if not html:
                print(f"Failed to fetch page {page}. Stopping search.")
                break
            
            jobs = self.parser.parse_search_results(html)
            
            if not jobs:
                print(f"No jobs found on page {page}. Stopping search.")
                break
            
            all_jobs.extend(jobs)
            page += 1
        
        return all_jobs[:limit]

    def get_full_description(self, job: JobPosting) -> Optional[str]:
        """
        Fetch full job description for a posting.
        
        Args:
            job: JobPosting object with URL
            
        Returns:
            Full description text, or None if fetch fails
        """
        html = self.client.fetch_job_detail(job.url)
        if html:
            return self.parser.parse_job_detail(html)
        return None
