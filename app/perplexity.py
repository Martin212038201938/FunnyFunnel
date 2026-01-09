"""
Perplexity AI Service for company research.
Uses the Perplexity API to search for real company information.
"""
import os
import re
import json
import requests


class PerplexityService:
    """Service for researching company information using Perplexity AI."""

    def __init__(self):
        self.api_key = os.environ.get('PERPLEXITY_API_KEY')
        self.base_url = "https://api.perplexity.ai/chat/completions"

    def _call_api(self, prompt: str) -> str:
        """Make a call to the Perplexity API."""
        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY not configured")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "llama-3.1-sonar-small-128k-online",
            "messages": [
                {
                    "role": "system",
                    "content": "Du bist ein Recherche-Assistent für B2B-Vertrieb. Deine Aufgabe ist es, Firmendaten zu recherchieren und strukturiert zurückzugeben. Antworte immer auf Deutsch und liefere nur verifizierte Informationen. Wenn du etwas nicht findest, schreibe 'NICHT_GEFUNDEN'."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.1,
            "max_tokens": 1000
        }

        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            return data['choices'][0]['message']['content']
        except requests.exceptions.RequestException as e:
            print(f"Perplexity API error: {e}")
            raise

    def research_company(self, company_name: str, job_title: str = None, location: str = None) -> dict:
        """
        Research company information.

        Returns dict with:
        - firmen_website: Company website URL
        - firmen_adresse: Company address
        - firmen_email: Company email (from imprint)
        - ansprechpartner_name: Contact person name
        - ansprechpartner_rolle: Contact person role
        - ansprechpartner_linkedin: LinkedIn profile URL
        """
        # Build search context
        context_parts = [f"Firma: {company_name}"]
        if location:
            context_parts.append(f"Standort: {location}")
        if job_title:
            context_parts.append(f"Stellenanzeige: {job_title}")

        context = ", ".join(context_parts)

        prompt = f"""Recherchiere folgende Firmendaten für: {context}

Finde bitte:
1. Die offizielle Website der Firma
2. Die Firmenadresse (aus dem Impressum)
3. Eine Kontakt-E-Mail-Adresse (aus dem Impressum, bevorzugt info@ oder kontakt@)
4. Den Namen eines Entscheiders (CEO, CTO, Geschäftsführer, Head of HR, oder Head of Learning & Development)
5. Die Rolle/Position dieser Person
6. Den LinkedIn-Profil-Link dieser Person (falls vorhanden)

Antworte NUR im folgenden JSON-Format, ohne zusätzlichen Text:
{{
    "firmen_website": "https://...",
    "firmen_adresse": "Straße Nr, PLZ Stadt",
    "firmen_email": "email@firma.de",
    "ansprechpartner_name": "Vorname Nachname",
    "ansprechpartner_rolle": "Position",
    "ansprechpartner_linkedin": "https://linkedin.com/in/..."
}}

Falls du eine Information nicht findest, setze den Wert auf null.
"""

        try:
            response_text = self._call_api(prompt)

            # Try to extract JSON from response
            json_match = re.search(r'\{[^{}]*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())

                # Clean up results - replace "NICHT_GEFUNDEN" or empty strings with None
                for key in result:
                    if result[key] in [None, "", "NICHT_GEFUNDEN", "null", "nicht gefunden", "Nicht gefunden"]:
                        result[key] = None
                    elif result[key] and "NICHT_GEFUNDEN" in str(result[key]):
                        result[key] = None

                return result
            else:
                print(f"Could not parse JSON from response: {response_text}")
                return {}

        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
            return {}
        except Exception as e:
            print(f"Research error: {e}")
            raise

    def find_decision_maker(self, company_name: str, department: str = "IT") -> dict:
        """
        Find a specific decision maker at a company.

        Args:
            company_name: Name of the company
            department: Department to search (IT, HR, Learning & Development, etc.)

        Returns dict with contact person details.
        """
        prompt = f"""Finde einen Entscheider bei der Firma "{company_name}" im Bereich {department}.

Suche nach Personen mit Titeln wie:
- CEO, CTO, CIO, CDO (Chief Digital Officer)
- Head of {department}
- VP {department}
- Director {department}
- Leiter {department}

Antworte NUR im folgenden JSON-Format:
{{
    "name": "Vorname Nachname",
    "rolle": "Position/Titel",
    "linkedin": "https://linkedin.com/in/...",
    "quelle": "Woher die Information stammt"
}}

Falls du niemanden findest, setze alle Werte auf null.
"""

        try:
            response_text = self._call_api(prompt)

            json_match = re.search(r'\{[^{}]*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())

                # Clean up
                for key in result:
                    if result[key] in [None, "", "NICHT_GEFUNDEN", "null"]:
                        result[key] = None

                return result
            return {}

        except Exception as e:
            print(f"Decision maker search error: {e}")
            return {}
