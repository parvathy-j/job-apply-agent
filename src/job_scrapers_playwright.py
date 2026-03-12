"""Playwright-based job scrapers for LinkedIn, Seek, and Glassdoor."""

import os
import asyncio
from typing import Optional
from dataclasses import dataclass

from playwright.async_api import async_playwright, Browser, Page


@dataclass
class JobPosting:
    """Represents a single job posting."""
    title: str
    company: str
    location: str
    description: str
    url: str
    salary: Optional[str] = None


class LinkedInScraper:
    """Playwright-based LinkedIn job scraper."""

    def __init__(self, headless: bool = True):
        """
        Initialize LinkedIn scraper.
        
        Args:
            headless: Run browser in headless mode (no visible window)
        """
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.user_agent = os.getenv("USER_AGENT", 
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

    async def launch_browser(self):
        """Launch Playwright browser instance."""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=self.headless)

    async def close_browser(self):
        """Close browser instance."""
        if self.browser:
            await self.browser.close()

    async def search(self, query: str, location: str, limit: int = 10) -> list[JobPosting]:
        """
        Search LinkedIn for jobs.
        
        Args:
            query: Job search query
            location: Job location
            limit: Maximum number of jobs to retrieve
            
        Returns:
            List of JobPosting objects
        """
        if not self.browser:
            await self.launch_browser()

        page = await self.browser.new_page()
        page.set_extra_http_headers({"User-Agent": self.user_agent})
        
        jobs = []
        try:
            # LinkedIn search URL
            search_url = f"https://www.linkedin.com/jobs/search/?keywords={query}&location={location}"
            await page.goto(search_url, wait_until="networkidle", timeout=30000)
            
            # Wait for job listings to load
            await page.wait_for_selector(".base-search-card", timeout=10000)
            
            # Scroll to load more jobs
            for _ in range(limit // 10 + 1):
                await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
                await page.wait_for_timeout(1000)
            
            # Extract job listings
            job_elements = await page.query_selector_all(".base-search-card")
            
            for elem in job_elements[:limit]:
                try:
                    # Extract title
                    title_elem = await elem.query_selector("h3")
                    title = await title_elem.text_content() if title_elem else "Unknown"
                    
                    # Extract company
                    company_elem = await elem.query_selector(".base-search-card__subtitle")
                    company = await company_elem.text_content() if company_elem else "Unknown"
                    
                    # Extract location
                    location_elem = await elem.query_selector(".job-search-card__location")
                    job_location = await location_elem.text_content() if location_elem else "Unknown"
                    
                    # Extract job URL
                    link_elem = await elem.query_selector("a")
                    job_url = await link_elem.get_attribute("href") if link_elem else ""
                    
                    # Click to load full description
                    await elem.click()
                    await page.wait_for_timeout(500)
                    
                    # Extract full description
                    description_elem = await page.query_selector(".show-more-less-html__markup")
                    description = await description_elem.text_content() if description_elem else ""
                    
                    # Extract salary if available
                    salary_elem = await page.query_selector(".salary-main-pay")
                    salary = await salary_elem.text_content() if salary_elem else None
                    
                    job = JobPosting(
                        title=title.strip(),
                        company=company.strip(),
                        location=job_location.strip(),
                        description=description.strip(),
                        url=job_url.strip(),
                        salary=salary.strip() if salary else None,
                    )
                    jobs.append(job)
                    
                except Exception as e:
                    print(f"Error extracting LinkedIn job: {e}")
                    continue
        
        except Exception as e:
            print(f"Error searching LinkedIn: {e}")
        
        finally:
            await page.close()
        
        return jobs


class SeekScraper:
    """Playwright-based Seek job scraper (Australian job board)."""

    def __init__(self, headless: bool = True):
        """
        Initialize Seek scraper.
        
        Args:
            headless: Run browser in headless mode (no visible window)
        """
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.user_agent = os.getenv("USER_AGENT", 
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

    async def launch_browser(self):
        """Launch Playwright browser instance."""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=self.headless)

    async def close_browser(self):
        """Close browser instance."""
        if self.browser:
            await self.browser.close()

    async def search(self, query: str, location: str, limit: int = 10) -> list[JobPosting]:
        """
        Search Seek for jobs.
        
        Args:
            query: Job search query
            location: Job location (e.g., "Sydney", "Melbourne")
            limit: Maximum number of jobs to retrieve
            
        Returns:
            List of JobPosting objects
        """
        if not self.browser:
            await self.launch_browser()

        page = await self.browser.new_page()
        page.set_extra_http_headers({"User-Agent": self.user_agent})
        
        jobs = []
        try:
            # Seek search URL
            search_url = f"https://www.seek.com.au/{query}-jobs/in-{location}"
            await page.goto(search_url, wait_until="networkidle", timeout=30000)
            
            # Wait for job listings to load
            await page.wait_for_selector("[data-testid='job-list-item']", timeout=10000)
            
            # Scroll to load more jobs
            for _ in range(limit // 20 + 1):
                await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
                await page.wait_for_timeout(1000)
            
            # Extract job listings
            job_elements = await page.query_selector_all("[data-testid='job-list-item']")
            
            for elem in job_elements[:limit]:
                try:
                    # Extract title
                    title_elem = await elem.query_selector("[data-testid='job-title']")
                    title = await title_elem.text_content() if title_elem else "Unknown"
                    
                    # Extract company
                    company_elem = await elem.query_selector("[data-testid='job-company']")
                    company = await company_elem.text_content() if company_elem else "Unknown"
                    
                    # Extract location
                    location_elem = await elem.query_selector("[data-testid='job-location']")
                    job_location = await location_elem.text_content() if location_elem else "Unknown"
                    
                    # Extract job URL
                    link_elem = await elem.query_selector("a")
                    job_url = await link_elem.get_attribute("href") if link_elem else ""
                    if job_url and not job_url.startswith("http"):
                        job_url = "https://www.seek.com.au" + job_url
                    
                    # Extract snippet (Seek shows snippet in list view)
                    snippet_elem = await elem.query_selector("[data-testid='job-summary']")
                    description = await snippet_elem.text_content() if snippet_elem else ""
                    
                    # Extract salary if available
                    salary_elem = await elem.query_selector("[data-testid='job-salary']")
                    salary = await salary_elem.text_content() if salary_elem else None
                    
                    job = JobPosting(
                        title=title.strip(),
                        company=company.strip(),
                        location=job_location.strip(),
                        description=description.strip(),
                        url=job_url.strip(),
                        salary=salary.strip() if salary else None,
                    )
                    jobs.append(job)
                    
                except Exception as e:
                    print(f"Error extracting Seek job: {e}")
                    continue
        
        except Exception as e:
            print(f"Error searching Seek: {e}")
        
        finally:
            await page.close()
        
        return jobs


class GlassdoorScraper:
    """Playwright-based Glassdoor job scraper."""

    def __init__(self, headless: bool = True):
        """
        Initialize Glassdoor scraper.
        
        Args:
            headless: Run browser in headless mode (no visible window)
        """
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.user_agent = os.getenv("USER_AGENT", 
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")

    async def launch_browser(self):
        """Launch Playwright browser instance."""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=self.headless)

    async def close_browser(self):
        """Close browser instance."""
        if self.browser:
            await self.browser.close()

    async def search(self, query: str, location: str, limit: int = 10) -> list[JobPosting]:
        """
        Search Glassdoor for jobs.
        
        Args:
            query: Job search query
            location: Job location
            limit: Maximum number of jobs to retrieve
            
        Returns:
            List of JobPosting objects
        """
        if not self.browser:
            await self.launch_browser()

        page = await self.browser.new_page()
        page.set_extra_http_headers({"User-Agent": self.user_agent})
        
        jobs = []
        try:
            # Glassdoor search URL
            search_url = f"https://www.glassdoor.com.au/Job/jobs-{query}-in-{location}.htm"
            await page.goto(search_url, wait_until="networkidle", timeout=30000)
            
            # Wait for job listings to load
            await page.wait_for_selector("[data-test='jobCard']", timeout=10000)
            
            # Scroll to load more jobs
            for _ in range(limit // 30 + 1):
                await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
                await page.wait_for_timeout(1000)
            
            # Extract job listings
            job_elements = await page.query_selector_all("[data-test='jobCard']")
            
            for elem in job_elements[:limit]:
                try:
                    # Extract title
                    title_elem = await elem.query_selector("[data-test='jobTitle']")
                    title = await title_elem.text_content() if title_elem else "Unknown"
                    
                    # Extract company
                    company_elem = await elem.query_selector("[data-test='companyName']")
                    company = await company_elem.text_content() if company_elem else "Unknown"
                    
                    # Extract location
                    location_elem = await elem.query_selector("[data-test='job-location']")
                    job_location = await location_elem.text_content() if location_elem else "Unknown"
                    
                    # Extract job URL
                    link_elem = await elem.query_selector("a")
                    job_url = await link_elem.get_attribute("href") if link_elem else ""
                    if job_url and not job_url.startswith("http"):
                        job_url = "https://www.glassdoor.com.au" + job_url
                    
                    # Extract summary
                    summary_elem = await elem.query_selector("[data-test='jobSummary']")
                    description = await summary_elem.text_content() if summary_elem else ""
                    
                    # Extract salary if available
                    salary_elem = await elem.query_selector("[data-test='salaryEstimate']")
                    salary = await salary_elem.text_content() if salary_elem else None
                    
                    job = JobPosting(
                        title=title.strip(),
                        company=company.strip(),
                        location=job_location.strip(),
                        description=description.strip(),
                        url=job_url.strip(),
                        salary=salary.strip() if salary else None,
                    )
                    jobs.append(job)
                    
                except Exception as e:
                    print(f"Error extracting Glassdoor job: {e}")
                    continue
        
        except Exception as e:
            print(f"Error searching Glassdoor: {e}")
        
        finally:
            await page.close()
        
        return jobs


async def main():
    """Example usage of Playwright scrapers."""
    # LinkedIn example
    linkedin = LinkedInScraper()
    linkedin_jobs = await linkedin.search("Python Developer", "Sydney", limit=5)
    print(f"Found {len(linkedin_jobs)} jobs on LinkedIn")
    for job in linkedin_jobs:
        print(f"  - {job.title} at {job.company}")
    await linkedin.close_browser()
    
    # Seek example
    seek = SeekScraper()
    seek_jobs = await seek.search("python developer", "Sydney", limit=5)
    print(f"Found {len(seek_jobs)} jobs on Seek")
    for job in seek_jobs:
        print(f"  - {job.title} at {job.company}")
    await seek.close_browser()
    
    # Glassdoor example
    glassdoor = GlassdoorScraper()
    glassdoor_jobs = await glassdoor.search("Python Developer", "Sydney", limit=5)
    print(f"Found {len(glassdoor_jobs)} jobs on Glassdoor")
    for job in glassdoor_jobs:
        print(f"  - {job.title} at {job.company}")
    await glassdoor.close_browser()


if __name__ == "__main__":
    asyncio.run(main())
