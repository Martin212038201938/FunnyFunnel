"""
StepStone Job Search Service

Scrapes job listings from StepStone.de based on search criteria.
Falls back to demo data if scraping is not possible.
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import urlencode, quote_plus
from datetime import datetime, timedelta
import re
import json
import time
import random


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

    # Demo job data for when scraping is not possible
    DEMO_JOBS = [
        {
            'titel': 'Senior AI Engineer - Large Language Models (m/w/d)',
            'firmenname': 'TechVision AI GmbH',
            'standort': 'Berlin',
            'textvorschau': '''Wir suchen einen erfahrenen AI Engineer für die Entwicklung und Optimierung von LLM-basierten Anwendungen.

Ihre Aufgaben:
• Entwicklung und Fine-Tuning von Large Language Models (GPT-4, Claude, Llama)
• Integration von LLMs in bestehende Unternehmensanwendungen
• Optimierung von Inference-Pipelines für Produktion
• Zusammenarbeit mit dem Produktteam zur Definition von AI-Features
• Mentoring von Junior-Entwicklern

Ihr Profil:
• Mindestens 5 Jahre Erfahrung in Machine Learning / AI
• Fundierte Kenntnisse in Python, PyTorch oder TensorFlow
• Erfahrung mit LLM-APIs (OpenAI, Anthropic, Hugging Face)
• Kenntnisse in MLOps und Cloud-Infrastruktur (AWS, GCP, Azure)
• Sehr gute Deutsch- und Englischkenntnisse

Wir bieten:
• Attraktives Gehalt: 85.000 - 120.000 EUR
• Remote-First Kultur mit optionalem Büro in Berlin-Mitte
• 30 Tage Urlaub + Bildungsbudget
• Modernste Hardware und Software-Tools
• Regelmäßige Team-Events und Konferenzbesuche''',
            'keywords': ['AI', 'LLM', 'GPT', 'Machine Learning'],
        },
        {
            'titel': 'Machine Learning Engineer - Computer Vision',
            'firmenname': 'Automotive AI Solutions',
            'standort': 'München',
            'textvorschau': '''Entwicklung von Computer Vision Lösungen für autonomes Fahren bei einem führenden Automotive-Zulieferer.

Ihre Aufgaben:
• Entwicklung von Objekterkennungs- und Tracking-Algorithmen
• Training und Optimierung von Deep Learning Modellen für Echtzeit-Anwendungen
• Integration von Computer Vision in eingebettete Systeme
• Zusammenarbeit mit Hardware-Teams für optimale Performance
• Evaluation und Benchmarking von ML-Modellen

Ihr Profil:
• Master/PhD in Informatik, Mathematik oder verwandtem Bereich
• 3+ Jahre Erfahrung in Computer Vision und Deep Learning
• Expertise in PyTorch/TensorFlow und OpenCV
• Erfahrung mit YOLO, Faster R-CNN oder ähnlichen Architekturen
• Kenntnisse in C++ und eingebetteten Systemen von Vorteil

Wir bieten:
• Gehalt: 75.000 - 100.000 EUR
• Flexible Arbeitszeiten, 2 Tage Home Office
• Betriebliche Altersvorsorge
• Firmenwagen oder Mobilitätsbudget
• Weiterbildungsmöglichkeiten und Konferenzbesuche''',
            'keywords': ['Machine Learning', 'Computer Vision', 'Deep Learning', 'AI'],
        },
        {
            'titel': 'Data Scientist - Generative AI (m/w/d)',
            'firmenname': 'FinTech Innovation Lab',
            'standort': 'Frankfurt am Main',
            'textvorschau': '''Implementierung von GenAI-Lösungen im Finanzsektor bei einem innovativen FinTech-Unternehmen.

Ihre Aufgaben:
• Entwicklung von GenAI-Anwendungen für Finanzanalyse und Risikobewertung
• Analyse großer Datenmengen und Entwicklung prädiktiver Modelle
• Integration von LLMs für automatisierte Berichtserstellung
• Zusammenarbeit mit Compliance-Teams für regulatorische Anforderungen
• Präsentation von Ergebnissen an Stakeholder und Management

Ihr Profil:
• Master in Data Science, Statistik oder Informatik
• 4+ Jahre Erfahrung als Data Scientist
• Kenntnisse in GenAI/LLM-Technologien
• Erfahrung im Finanzsektor von Vorteil
• SQL, Python, und Visualisierungstools (Tableau, PowerBI)

Wir bieten:
• Gehalt: 80.000 - 110.000 EUR + Bonus
• Zentrale Lage in Frankfurt
• Flexible Arbeitszeiten
• Betriebliche Krankenversicherung
• Startup-Kultur mit flachen Hierarchien''',
            'keywords': ['GenAI', 'Data Science', 'AI', 'Machine Learning'],
        },
        {
            'titel': 'KI-Projektmanager - Digital Transformation',
            'firmenname': 'Consulting Partners AG',
            'standort': 'Hamburg',
            'textvorschau': '''Leitung von KI-Transformationsprojekten bei Großkunden als Senior Consultant.

Ihre Aufgaben:
• Leitung von KI-Einführungsprojekten bei DAX-Unternehmen
• Entwicklung von KI-Strategien und Roadmaps
• Beratung zu Copilot, ChatGPT Enterprise und anderen AI-Tools
• Stakeholder-Management und Change Management
• Aufbau und Führung von Projektteams

Ihr Profil:
• 5+ Jahre Erfahrung in IT-Beratung oder Projektmanagement
• Verständnis von KI/ML-Technologien und deren Anwendung
• Erfahrung mit Microsoft 365 Copilot, ChatGPT Enterprise
• Zertifizierungen (PMP, PRINCE2) von Vorteil
• Exzellente Kommunikations- und Präsentationsfähigkeiten

Wir bieten:
• Gehalt: 90.000 - 130.000 EUR
• Firmenwagen oder BahnCard 100
• Home Office und flexible Arbeitszeiten
• Umfangreiche Weiterbildungsprogramme
• Internationales Arbeitsumfeld''',
            'keywords': ['KI', 'Copilot', 'ChatGPT', 'AI'],
        },
        {
            'titel': 'Prompt Engineer - Enterprise AI',
            'firmenname': 'Digital Solutions GmbH',
            'standort': 'Köln',
            'textvorschau': '''Optimierung von LLM-Prompts für Unternehmensanwendungen in einer spezialisierten AI-Agentur.

Ihre Aufgaben:
• Entwicklung und Optimierung von Prompts für verschiedene LLMs
• Erstellung von Prompt-Bibliotheken und Best Practices
• A/B-Testing und Performance-Analyse von Prompts
• Schulung von Kunden und internen Teams
• Dokumentation und Qualitätssicherung

Ihr Profil:
• 2+ Jahre Erfahrung mit LLMs und Prompt Engineering
• Tiefes Verständnis von GPT-4, Claude, Gemini und anderen Modellen
• Kenntnisse in Python für Automatisierung
• Kreativität und analytisches Denken
• Sehr gute Deutsch- und Englischkenntnisse

Wir bieten:
• Gehalt: 60.000 - 85.000 EUR
• 100% Remote möglich
• Flexible Arbeitszeiten
• Neueste AI-Tools und Technologien
• Startup-Atmosphäre mit schnellem Wachstum''',
            'keywords': ['Prompt Engineer', 'LLM', 'AI', 'GenAI'],
        },
        {
            'titel': 'Head of AI & Innovation',
            'firmenname': 'Enterprise Tech AG',
            'standort': 'Düsseldorf',
            'textvorschau': '''Führung des AI-Teams und strategische Ausrichtung der KI-Initiativen als Teil der Geschäftsleitung.

Ihre Aufgaben:
• Strategische Führung des AI-Teams (15+ Mitarbeiter)
• Entwicklung der AI-Roadmap und Vision
• Budget- und Ressourcenplanung
• Zusammenarbeit mit C-Level und Stakeholdern
• Aufbau von Partnerschaften mit Technologieanbietern

Ihr Profil:
• 10+ Jahre Erfahrung in AI/ML
• 5+ Jahre Führungserfahrung
• Nachweisliche Erfolge bei AI-Transformationen
• MBA oder vergleichbare Qualifikation von Vorteil
• Starke strategische und kommunikative Fähigkeiten

Wir bieten:
• Gehalt: 150.000 - 200.000 EUR + Bonus
• Geschäftswagen
• Aktienoptionen
• Executive Coaching
• Internationale Reisetätigkeit''',
            'keywords': ['AI', 'KI', 'Machine Learning', 'Leadership'],
        },
        {
            'titel': 'NLP Engineer - Conversational AI',
            'firmenname': 'ChatBot Innovations',
            'standort': 'Berlin',
            'textvorschau': '''Entwicklung von Chatbots und virtuellen Assistenten für Enterprise-Kunden.

Ihre Aufgaben:
• Entwicklung von NLU/NLG-Komponenten
• Training und Optimierung von Conversational AI Modellen
• Integration mit Backend-Systemen (CRM, ERP)
• Performance-Monitoring und kontinuierliche Verbesserung
• Technische Dokumentation

Ihr Profil:
• 3+ Jahre Erfahrung in NLP/Conversational AI
• Kenntnisse in Rasa, Dialogflow oder ähnlichen Frameworks
• Python, FastAPI, Docker
• Erfahrung mit LLM-Integration
• Teamfähigkeit und selbstständige Arbeitsweise

Wir bieten:
• Gehalt: 65.000 - 90.000 EUR
• Zentrale Lage in Berlin-Kreuzberg
• Flexible Arbeitszeiten, Home Office möglich
• Regelmäßige Hackathons
• Weiterbildungsbudget''',
            'keywords': ['NLP', 'AI', 'Conversational AI', 'LLM'],
        },
        {
            'titel': 'AI Solutions Architect (m/w/d)',
            'firmenname': 'Cloud Systems GmbH',
            'standort': 'Stuttgart',
            'textvorschau': '''Design und Implementierung skalierbarer AI-Lösungen in der Cloud.

Ihre Aufgaben:
• Architektur-Design für AI/ML-Systeme
• Beratung von Kunden bei der Cloud-Migration
• Implementierung von MLOps-Pipelines
• Performance-Optimierung und Kostenkontrolle
• Technische Führung von Projektteams

Ihr Profil:
• 7+ Jahre Erfahrung in Software-Architektur
• Expertise in AWS, Azure oder GCP
• Kenntnisse in Kubernetes, Terraform, CI/CD
• Erfahrung mit ML-Frameworks und MLOps
• AWS/Azure/GCP Zertifizierungen von Vorteil

Wir bieten:
• Gehalt: 95.000 - 130.000 EUR
• Remote-First mit optionalem Büro
• Zertifizierungsbudget
• Moderne Arbeitsausstattung
• Team-Events und Workations''',
            'keywords': ['AI', 'Cloud', 'Machine Learning', 'Architecture'],
        },
        {
            'titel': 'Deep Learning Researcher',
            'firmenname': 'Research Institute AI',
            'standort': 'München',
            'textvorschau': '''Forschung im Bereich Deep Learning und neuronale Netze an einem führenden Forschungsinstitut.

Ihre Aufgaben:
• Grundlagenforschung in Deep Learning
• Entwicklung neuer Algorithmen und Architekturen
• Publikation in Top-Konferenzen (NeurIPS, ICML, ICLR)
• Betreuung von PhD-Studenten
• Zusammenarbeit mit Industriepartnern

Ihr Profil:
• PhD in Machine Learning, Informatik oder Mathematik
• Publikationstrack Record in Top-Venues
• Expertise in PyTorch/JAX
• Erfahrung mit GPU-Cluster und verteiltem Training
• Leidenschaft für Forschung

Wir bieten:
• Gehalt: 70.000 - 100.000 EUR
• Akademisches Umfeld mit Industrieanbindung
• Zugang zu modernster GPU-Infrastruktur
• Konferenzreisen weltweit
• Flexible Arbeitszeiten''',
            'keywords': ['Deep Learning', 'AI', 'Neural Network', 'Research'],
        },
        {
            'titel': 'MLOps Engineer - AI Platform',
            'firmenname': 'DataDriven Tech',
            'standort': 'Leipzig',
            'textvorschau': '''Aufbau und Betrieb der ML-Infrastruktur für skalierbare AI-Produkte.

Ihre Aufgaben:
• Aufbau und Wartung der ML-Plattform
• Implementierung von CI/CD für ML-Modelle
• Monitoring und Alerting für ML-Systeme
• Optimierung von Training- und Inference-Pipelines
• Zusammenarbeit mit Data Scientists

Ihr Profil:
• 4+ Jahre Erfahrung in DevOps/MLOps
• Kubernetes, Docker, Helm
• MLflow, Kubeflow oder ähnliche Tools
• Python, Bash, Terraform
• Cloud-Erfahrung (AWS/GCP/Azure)

Wir bieten:
• Gehalt: 70.000 - 95.000 EUR
• Remote-First Kultur
• 30 Tage Urlaub
• Weiterbildungsbudget
• Stock Options''',
            'keywords': ['MLOps', 'Machine Learning', 'AI', 'DevOps'],
        },
    ]

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
        Falls back to demo data if scraping fails.
        """
        # Try real scraping first
        try:
            all_jobs = self._scrape_jobs(keywords, location, radius, max_pages, date_filter, job_title_filter)
            if all_jobs:
                return all_jobs
        except Exception as e:
            print(f"Scraping failed, using demo data: {e}")

        # Fallback to demo data
        return self._get_demo_jobs(keywords, location, job_title_filter)

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

    def _get_demo_jobs(self, keywords=None, location=None, job_title_filter=None):
        """Generate demo job data based on search criteria."""
        jobs = []

        for i, demo in enumerate(self.DEMO_JOBS):
            job = demo.copy()
            job['quelle'] = 'StepStone'
            job['quelle_url'] = f'https://www.stepstone.de/stellenangebote--Demo-{i+1}-{job["standort"]}'

            # Filter by location if specified
            if location:
                location_lower = location.lower()
                if location_lower not in job['standort'].lower():
                    # 30% chance to include anyway for variety
                    if random.random() > 0.3:
                        continue
                    job['standort'] = location.title()

            # Filter by keywords if specified
            if keywords:
                keywords_lower = keywords.lower()
                title_lower = job['titel'].lower()
                preview_lower = job['textvorschau'].lower()

                # Check if any keyword matches
                keyword_list = keywords_lower.replace(',', ' ').split()
                matches = any(kw in title_lower or kw in preview_lower for kw in keyword_list)

                if not matches:
                    continue

            # Filter by job title if specified
            if job_title_filter:
                if job_title_filter.lower() not in job['titel'].lower():
                    continue

            jobs.append(job)

        # If no matches, return all demo jobs
        if not jobs:
            jobs = []
            for i, demo in enumerate(self.DEMO_JOBS):
                job = demo.copy()
                job['quelle'] = 'StepStone'
                job['quelle_url'] = f'https://www.stepstone.de/stellenangebote--Demo-{i+1}-{demo["standort"]}'
                if location:
                    job['standort'] = location.title()
                jobs.append(job)

        return jobs

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
