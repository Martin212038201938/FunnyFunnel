# FunnyFunnel

Sales Lead Generator für KI-Jobanzeigen auf StepStone.

## Features

- **Lead-Dashboard**: Zentrale Übersicht aller gesammelten Jobanzeigen
- **Checkbox-Aktivierung**: Manuelle Freigabe für externe Recherchen
- **Automatische Recherche**: Firmen- & Impressumsrecherche (Adresse, E-Mail)
- **Entscheider-Suche**: LinkedIn-Recherche nach CEO, CTO, CIO, Head of L&D
- **Anschreiben-Generator**: Personalisierte Entwürfe per Template
- **Status-Workflow**: neu → aktiviert → recherchiert → Anschreiben erstellt → angeschrieben → Antwort erhalten
- **CSV-Export**: Alle Lead-Daten exportierbar

## Tech Stack

- **Backend**: Python Flask
- **Database**: SQLite (single-user optimiert)
- **Frontend**: Vanilla HTML/CSS/JS
- **Deployment**: AlwaysData-kompatibel

## Installation

### Lokal

```bash
# Repository klonen
git clone <repo-url>
cd FunnyFunnel

# Virtual Environment erstellen
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# oder: venv\Scripts\activate  # Windows

# Dependencies installieren
pip install -r requirements.txt

# Environment-Variablen konfigurieren
cp .env.example .env

# Anwendung starten
python run.py
```

Die App ist dann unter http://localhost:5000 erreichbar.

### AlwaysData Deployment

1. **SSH-Zugang** zu AlwaysData einrichten
2. **Repository** in das Web-Verzeichnis klonen
3. **Virtual Environment** erstellen und aktivieren
4. **Dependencies** installieren: `pip install -r requirements.txt`
5. **WSGI konfigurieren** (AlwaysData Admin Panel):
   - Python-Version auswählen
   - WSGI-Datei: `/path/to/wsgi.py`
   - Working Directory entsprechend setzen

## Nutzung

1. **Demo-Daten laden**: Klick auf "Demo-Daten laden" für Beispiel-Leads
2. **Lead aktivieren**: Checkbox anklicken um Recherche freizugeben
3. **Recherchieren**: Button "Recherchieren" für Firmen- und Kontaktdaten
4. **Anschreiben erstellen**: Button "Anschreiben erstellen" für personalisierten Entwurf
5. **Status ändern**: Dropdown zur manuellen Statusänderung
6. **CSV-Export**: Alle Leads als CSV herunterladen

## API Endpoints

| Methode | Endpoint | Beschreibung |
|---------|----------|--------------|
| GET | `/api/leads` | Alle Leads abrufen (Filter: `?status=`, `?keyword=`) |
| POST | `/api/leads` | Neuen Lead erstellen |
| GET | `/api/leads/<id>` | Einzelnen Lead abrufen |
| PUT | `/api/leads/<id>` | Lead aktualisieren |
| DELETE | `/api/leads/<id>` | Lead löschen |
| POST | `/api/leads/<id>/activate` | Lead aktivieren |
| POST | `/api/leads/<id>/research` | Recherche starten |
| POST | `/api/leads/<id>/generate-letter` | Anschreiben generieren |
| PUT | `/api/leads/<id>/status` | Status ändern |
| GET | `/api/leads/export` | CSV-Export |
| POST | `/api/seed-demo` | Demo-Daten laden |

## Projektstruktur

```
FunnyFunnel/
├── app/
│   ├── __init__.py      # Flask App Factory
│   ├── models.py        # SQLAlchemy Models
│   ├── routes.py        # API & View Routes
│   └── templates/
│       └── index.html   # Dashboard Template
├── static/
│   ├── css/
│   │   └── style.css    # Styles
│   └── js/
│       └── app.js       # Frontend Logic
├── run.py               # Development Server
├── wsgi.py              # Production WSGI Entry
├── requirements.txt     # Dependencies
├── .env.example         # Environment Template
└── README.md
```

## Hinweise

- **Single-User**: Konzipiert für einen einzelnen Vertriebsmitarbeiter
- **Performance**: Lazy Loading, keine unnötigen externen Aufrufe
- **MVP**: Recherche-Funktionen sind aktuell simuliert (Demo-Modus)
- **Sicherheit**: Kein Login erforderlich (interne Nutzung)

## Erweiterungsmöglichkeiten

- Echte StepStone API-Integration
- LinkedIn API für Entscheider-Recherche
- OpenAI/Claude API für KI-generierte Anschreiben
- E-Mail-Versand direkt aus der App
