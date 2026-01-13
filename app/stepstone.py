"""
StepStone Job Search Service

Scrapes job listings from StepStone.de based on search criteria.
Returns empty list if scraping fails - no demo data fallback.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlencode, quote_plus
from datetime import datetime, timedelta
import re
import json
import time


class StepStoneService:
    """Service to search and fetch job listings from StepStone."""

    BASE_URL = "https://www.stepstone.de"
    SEARCH_URL = f"{BASE_URL}/jobs"

    # Default headers to mimic browser
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

    # AI/KI related keywords for filtering
    AI_KEYWORDS = [
        'KI', 'AI', 'Künstliche Intelligenz', 'Artificial Intelligence',
        'Machine Learning', 'ML', 'Deep Learning', 'GenAI', 'Generative AI',
        'LLM', 'Large Language Model', 'ChatGPT', 'GPT', 'Copilot',
        'NLP', 'Natural Language Processing', 'Computer Vision',
        'Neural Network', 'Data Science', 'Prompt Engineer'
    ]

    # German regions/states
    REGIONS = {
        'baden-wuerttemberg': 'Baden-Württemberg',
        'bayern': 'Bayern',
        'berlin': 'Berlin',
        'brandenburg': 'Brandenburg',
        'bremen': 'Bremen',
        'hamburg': 'Hamburg',
        'hessen': 'Hessen',
        'mecklenburg-vorpommern': 'Mecklenburg-Vorpommern',
        'niedersachsen': 'Niedersachsen',
        'nordrhein-westfalen': 'Nordrhein-Westfalen',
        'rheinland-pfalz': 'Rheinland-Pfalz',
        'saarland': 'Saarland',
        'sachsen': 'Sachsen',
        'sachsen-anhalt': 'Sachsen-Anhalt',
        'schleswig-holstein': 'Schleswig-Holstein',
        'thueringen': 'Thüringen'
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    def build_search_url(self, keywords=None, location=None, radius=None, page=1, date_filter=None):
        """Build StepStone search URL with parameters."""
        url_parts = [self.SEARCH_URL]

        if keywords:
            url_parts.append(quote_plus(keywords))

        if location:
            url_parts.append(f"in-{quote_plus(location)}")

        url = "/".join(url_parts)

        params = {}
        if radius:
            params['radius'] = radius
        if page > 1:
            params['page'] = page
        if date_filter:
            params['age'] = date_filter

        if params:
            url += "?" + urlencode(params)

        return url

    def search_jobs(self, keywords=None, location=None, radius=30, max_pages=3, date_filter=None, job_title_filter=None):
        """
        Search for jobs on StepStone.
        Returns empty list if scraping fails - no demo data fallback.
        """
        try:
            all_jobs = self._scrape_jobs(keywords, location, radius, max_pages, date_filter, job_title_filter)
            return all_jobs if all_jobs else []
        except Exception as e:
            print(f"Scraping failed: {e}")
            return []

    def _scrape_jobs(self, keywords, location, radius, max_pages, date_filter, job_title_filter):
        """Attempt to scrape real jobs from StepStone."""
        all_jobs = []

        for page in range(1, max_pages + 1):
            url = self.build_search_url(
                keywords=keywords,
                location=location,
                radius=radius,
                page=page,
                date_filter=date_filter
            )

            response = self.session.get(url, timeout=15)
            response.raise_for_status()

            jobs = self._parse_search_results(response.text)

            if not jobs:
                break

            if job_title_filter:
                filter_lower = job_title_filter.lower()
                jobs = [j for j in jobs if filter_lower in j.get('titel', '').lower()]

            all_jobs.extend(jobs)

            if page < max_pages:
                time.sleep(1)

        # Remove duplicates
        seen_urls = set()
        unique_jobs = []
        for job in all_jobs:
            if job['quelle_url'] not in seen_urls:
                seen_urls.add(job['quelle_url'])
                unique_jobs.append(job)

        return unique_jobs

    def _parse_search_results(self, html):
        """Parse job listings from search results HTML."""
        soup = BeautifulSoup(html, 'lxml')
        jobs = []

        job_cards = soup.select('article[data-testid="job-item"]')
        if not job_cards:
            job_cards = soup.select('article.job-element')
        if not job_cards:
            job_cards = soup.select('[data-at="job-item"]')
        if not job_cards:
            job_cards = soup.select('a[href*="/stellenangebote--"]')

        for card in job_cards:
            try:
                job = self._extract_job_from_card(card, soup)
                if job:
                    jobs.append(job)
            except Exception as e:
                continue

        return jobs

    def _extract_job_from_card(self, card, soup):
        """Extract job data from a single job card element."""
        job = {
            'quelle': 'StepStone',
            'keywords': [],
        }

        title_elem = card.select_one('h2, h3, [data-at="job-item-title"], .job-element-title')
        if title_elem:
            job['titel'] = title_elem.get_text(strip=True)
        elif card.name == 'a':
            job['titel'] = card.get_text(strip=True)

        if not job.get('titel'):
            return None

        company_elem = card.select_one('[data-at="job-item-company-name"], .job-element-company, [data-testid="company-name"]')
        if company_elem:
            job['firmenname'] = company_elem.get_text(strip=True)

        location_elem = card.select_one('[data-at="job-item-location"], .job-element-location, [data-testid="job-item-location"]')
        if location_elem:
            job['standort'] = location_elem.get_text(strip=True)

        link_elem = card.select_one('a[href*="/stellenangebote"]') or (card if card.name == 'a' else None)
        if link_elem and link_elem.get('href'):
            href = link_elem['href']
            if href.startswith('/'):
                job['quelle_url'] = self.BASE_URL + href
            elif href.startswith('http'):
                job['quelle_url'] = href
            else:
                job['quelle_url'] = self.BASE_URL + '/' + href

        if not job.get('quelle_url'):
            return None

        snippet_elem = card.select_one('[data-at="job-item-snippet"], .job-element-snippet, [data-testid="job-item-snippet"]')
        if snippet_elem:
            job['textvorschau'] = snippet_elem.get_text(strip=True)[:500]

        title_lower = job['titel'].lower()
        for kw in self.AI_KEYWORDS:
            if kw.lower() in title_lower:
                job['keywords'].append(kw)

        return job

    def get_job_details(self, url):
        """Fetch full details for a single job posting."""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            return self._parse_job_details(response.text, url)
        except requests.RequestException as e:
            return None

    def _parse_job_details(self, html, url):
        """Parse full job details from job page HTML."""
        soup = BeautifulSoup(html, 'lxml')
        details = {}

        description_elem = soup.select_one('[data-at="job-ad-content"], .job-ad-content, [data-testid="job-ad-content"], .listing-content')
        if description_elem:
            details['volltext'] = description_elem.get_text(separator='\n', strip=True)

        company_section = soup.select_one('[data-at="company-info"], .company-info, [data-testid="company-info"]')
        if company_section:
            website_link = company_section.select_one('a[href*="http"]')
            if website_link:
                href = website_link.get('href', '')
                if 'stepstone' not in href:
                    details['firmen_website'] = href

        if details.get('volltext'):
            text_lower = details['volltext'].lower()
            keywords = []
            for kw in self.AI_KEYWORDS:
                if kw.lower() in text_lower:
                    keywords.append(kw)
            if keywords:
                details['keywords'] = keywords

        return details

    @classmethod
    def get_regions(cls):
        """Return list of available regions."""
        return cls.REGIONS

    @classmethod
    def get_ai_keywords(cls):
        """Return list of AI-related keywords."""
        return cls.AI_KEYWORDS


# Singleton instance
stepstone_service = StepStoneService()
