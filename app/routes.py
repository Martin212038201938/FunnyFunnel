from flask import Blueprint, jsonify, request, render_template, Response
from app import db
from app.models import Lead, LeadStatus
import csv
import io
from datetime import datetime

main_bp = Blueprint('main', __name__)
api_bp = Blueprint('api', __name__)


# Main route - serve the dashboard
@main_bp.route('/')
def index():
    return render_template('index.html')


# API Routes
@api_bp.route('/leads', methods=['GET'])
def get_leads():
    """Get all leads with optional filtering."""
    status_filter = request.args.get('status')
    keyword_filter = request.args.get('keyword')

    query = Lead.query

    if status_filter:
        query = query.filter(Lead.status == status_filter)

    if keyword_filter:
        query = query.filter(Lead.keywords.contains(keyword_filter))

    leads = query.order_by(Lead.erstellt_am.desc()).all()
    return jsonify([lead.to_dict() for lead in leads])


@api_bp.route('/leads/<int:lead_id>', methods=['GET'])
def get_lead(lead_id):
    """Get a single lead by ID."""
    lead = Lead.query.get_or_404(lead_id)
    return jsonify(lead.to_dict())


@api_bp.route('/leads', methods=['POST'])
def create_lead():
    """Create a new lead."""
    data = request.json

    lead = Lead(
        titel=data.get('titel'),
        quelle=data.get('quelle', 'StepStone'),
        quelle_url=data.get('quelle_url'),
        keywords=','.join(data.get('keywords', [])) if isinstance(data.get('keywords'), list) else data.get('keywords'),
        textvorschau=data.get('textvorschau'),
        firmenname=data.get('firmenname'),
        status=LeadStatus.NEU.value
    )

    db.session.add(lead)
    db.session.commit()

    return jsonify(lead.to_dict()), 201


@api_bp.route('/leads/<int:lead_id>', methods=['PUT'])
def update_lead(lead_id):
    """Update an existing lead."""
    lead = Lead.query.get_or_404(lead_id)
    data = request.json

    # Update fields if provided
    if 'titel' in data:
        lead.titel = data['titel']
    if 'quelle_url' in data:
        lead.quelle_url = data['quelle_url']
    if 'keywords' in data:
        lead.keywords = ','.join(data['keywords']) if isinstance(data['keywords'], list) else data['keywords']
    if 'textvorschau' in data:
        lead.textvorschau = data['textvorschau']
    if 'volltext' in data:
        lead.volltext = data['volltext']
    if 'firmenname' in data:
        lead.firmenname = data['firmenname']
    if 'firmen_website' in data:
        lead.firmen_website = data['firmen_website']
    if 'firmen_adresse' in data:
        lead.firmen_adresse = data['firmen_adresse']
    if 'firmen_email' in data:
        lead.firmen_email = data['firmen_email']
    if 'ansprechpartner_name' in data:
        lead.ansprechpartner_name = data['ansprechpartner_name']
    if 'ansprechpartner_rolle' in data:
        lead.ansprechpartner_rolle = data['ansprechpartner_rolle']
    if 'ansprechpartner_linkedin' in data:
        lead.ansprechpartner_linkedin = data['ansprechpartner_linkedin']
    if 'ansprechpartner_quelle' in data:
        lead.ansprechpartner_quelle = data['ansprechpartner_quelle']
    if 'anschreiben' in data:
        lead.anschreiben = data['anschreiben']
    if 'status' in data:
        lead.status = data['status']

    db.session.commit()
    return jsonify(lead.to_dict())


@api_bp.route('/leads/<int:lead_id>/activate', methods=['POST'])
def activate_lead(lead_id):
    """Activate a lead and trigger research."""
    lead = Lead.query.get_or_404(lead_id)

    if lead.status != LeadStatus.NEU.value:
        return jsonify({'error': 'Lead ist bereits aktiviert'}), 400

    lead.status = LeadStatus.AKTIVIERT.value
    db.session.commit()

    return jsonify(lead.to_dict())


@api_bp.route('/leads/<int:lead_id>/research', methods=['POST'])
def research_lead(lead_id):
    """
    Simulate research for a lead.
    In production, this would call external APIs for:
    - Full job posting text
    - Company website & imprint
    - LinkedIn profiles
    """
    lead = Lead.query.get_or_404(lead_id)

    if lead.status not in [LeadStatus.AKTIVIERT.value]:
        return jsonify({'error': 'Lead muss zuerst aktiviert werden'}), 400

    # Simulated research data (in production: real API calls)
    # Full text simulation
    lead.volltext = f"""
{lead.textvorschau or lead.titel}

Wir suchen eine/n engagierte/n Mitarbeiter/in für unser wachsendes Team.

Ihre Aufgaben:
- Entwicklung und Implementierung von KI-Lösungen
- Zusammenarbeit mit cross-funktionalen Teams
- Evaluation neuer Technologien im Bereich GenAI und Copilot

Ihr Profil:
- Erfahrung mit Machine Learning und KI-Technologien
- Kenntnisse in Python, TensorFlow oder PyTorch
- Begeisterung für innovative Technologien

Wir bieten:
- Flexible Arbeitszeiten
- Moderne Arbeitsumgebung
- Weiterbildungsmöglichkeiten
"""

    # Company research simulation
    if not lead.firmen_website:
        lead.firmen_website = f"https://www.{lead.firmenname.lower().replace(' ', '-')}.de" if lead.firmenname else None
    if not lead.firmen_adresse:
        lead.firmen_adresse = "Musterstraße 123, 10115 Berlin"
    if not lead.firmen_email:
        lead.firmen_email = f"info@{lead.firmenname.lower().replace(' ', '-')}.de" if lead.firmenname else None

    # Contact person simulation (CEO, CTO, CIO, Head of L&D)
    rollen = ['CEO', 'CTO', 'CIO', 'Head of Learning & Development', 'Chief Digital Officer']
    import random
    lead.ansprechpartner_name = random.choice(['Dr. Thomas Müller', 'Sarah Schmidt', 'Michael Weber', 'Anna Fischer', 'Christian Bauer'])
    lead.ansprechpartner_rolle = random.choice(rollen)
    lead.ansprechpartner_linkedin = f"https://linkedin.com/in/{lead.ansprechpartner_name.lower().replace(' ', '-').replace('.', '')}"
    lead.ansprechpartner_quelle = 'LinkedIn'

    lead.status = LeadStatus.RECHERCHIERT.value
    db.session.commit()

    return jsonify(lead.to_dict())


@api_bp.route('/leads/<int:lead_id>/generate-letter', methods=['POST'])
def generate_letter(lead_id):
    """Generate a personalized cover letter for a lead."""
    lead = Lead.query.get_or_404(lead_id)

    if lead.status not in [LeadStatus.RECHERCHIERT.value, LeadStatus.ANSCHREIBEN_ERSTELLT.value,
                           LeadStatus.ANGESCHRIEBEN.value, LeadStatus.ANTWORT_ERHALTEN.value]:
        return jsonify({'error': 'Lead muss zuerst recherchiert werden'}), 400

    # Get optional custom template from request
    data = request.json or {}
    absender_name = data.get('absender_name', '[Ihr Name]')
    absender_firma = data.get('absender_firma', '[Ihre Firma]')

    # Generate personalized letter
    lead.anschreiben = f"""Sehr geehrte/r {lead.ansprechpartner_name or 'Damen und Herren'},

mit großem Interesse habe ich Ihre Stellenanzeige "{lead.titel}" auf {lead.quelle} gelesen.

Als Experte im Bereich KI und digitale Transformation bin ich überzeugt, dass ich {lead.firmenname or 'Ihr Unternehmen'} bei der erfolgreichen Implementierung von KI-Lösungen unterstützen kann.

Besonders angesprochen hat mich:
- Der Fokus auf innovative KI-Technologien
- Die Möglichkeit, an zukunftsweisenden Projekten mitzuarbeiten
- Die Vision Ihres Unternehmens im Bereich digitaler Innovation

Ich würde mich sehr freuen, in einem persönlichen Gespräch zu erläutern, wie ich {lead.firmenname or 'Ihr Unternehmen'} mit meiner Expertise unterstützen kann.

Mit freundlichen Grüßen
{absender_name}
{absender_firma}
"""

    lead.status = LeadStatus.ANSCHREIBEN_ERSTELLT.value
    db.session.commit()

    return jsonify(lead.to_dict())


@api_bp.route('/leads/<int:lead_id>/status', methods=['PUT'])
def update_status(lead_id):
    """Update the status of a lead."""
    lead = Lead.query.get_or_404(lead_id)
    data = request.json

    new_status = data.get('status')
    if new_status not in Lead.get_status_options():
        return jsonify({'error': 'Ungültiger Status'}), 400

    lead.status = new_status
    db.session.commit()

    return jsonify(lead.to_dict())


@api_bp.route('/leads/<int:lead_id>', methods=['DELETE'])
def delete_lead(lead_id):
    """Delete a lead."""
    lead = Lead.query.get_or_404(lead_id)
    db.session.delete(lead)
    db.session.commit()
    return jsonify({'message': 'Lead gelöscht'}), 200


@api_bp.route('/leads/export', methods=['GET'])
def export_leads():
    """Export all leads as CSV."""
    leads = Lead.query.all()

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output, delimiter=';', quotechar='"')

    # Header
    writer.writerow([
        'ID', 'Titel', 'Quelle', 'URL', 'Keywords', 'Status',
        'Firmenname', 'Website', 'Adresse', 'E-Mail',
        'Ansprechpartner', 'Rolle', 'LinkedIn',
        'Anschreiben', 'Erstellt am', 'Aktualisiert am'
    ])

    # Data rows
    for lead in leads:
        writer.writerow([
            lead.id,
            lead.titel,
            lead.quelle,
            lead.quelle_url,
            lead.keywords,
            lead.status,
            lead.firmenname,
            lead.firmen_website,
            lead.firmen_adresse,
            lead.firmen_email,
            lead.ansprechpartner_name,
            lead.ansprechpartner_rolle,
            lead.ansprechpartner_linkedin,
            lead.anschreiben,
            lead.erstellt_am.isoformat() if lead.erstellt_am else '',
            lead.aktualisiert_am.isoformat() if lead.aktualisiert_am else ''
        ])

    output.seek(0)

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=leads_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'}
    )


@api_bp.route('/status-options', methods=['GET'])
def get_status_options():
    """Get all available status options."""
    return jsonify(Lead.get_status_options())


@api_bp.route('/seed-demo', methods=['POST'])
def seed_demo_data():
    """Seed database with demo data for testing."""
    demo_leads = [
        {
            'titel': 'AI Engineer - GenAI & Large Language Models (m/w/d)',
            'quelle': 'StepStone',
            'quelle_url': 'https://www.stepstone.de/stellenangebote--AI-Engineer-GenAI-Berlin',
            'keywords': 'GenAI,LLM,Python,Machine Learning',
            'textvorschau': 'Wir suchen einen erfahrenen AI Engineer für unser GenAI-Team...',
            'firmenname': 'TechVision GmbH'
        },
        {
            'titel': 'Senior Developer - Microsoft Copilot Integration',
            'quelle': 'StepStone',
            'quelle_url': 'https://www.stepstone.de/stellenangebote--Senior-Developer-Copilot-München',
            'keywords': 'Copilot,Microsoft,Azure,Integration',
            'textvorschau': 'Für unsere Digitalisierungsabteilung suchen wir einen Senior Developer...',
            'firmenname': 'Digital Solutions AG'
        },
        {
            'titel': 'KI-Projektmanager (m/w/d) - Schwerpunkt ChatGPT',
            'quelle': 'StepStone',
            'quelle_url': 'https://www.stepstone.de/stellenangebote--KI-Projektmanager-Hamburg',
            'keywords': 'KI,ChatGPT,Projektmanagement,Agile',
            'textvorschau': 'Als KI-Projektmanager leiten Sie innovative Projekte im Bereich ChatGPT...',
            'firmenname': 'Innovation Hub GmbH'
        },
        {
            'titel': 'Machine Learning Engineer - Computer Vision & GenAI',
            'quelle': 'StepStone',
            'quelle_url': 'https://www.stepstone.de/stellenangebote--ML-Engineer-Frankfurt',
            'keywords': 'Machine Learning,Computer Vision,GenAI,TensorFlow',
            'textvorschau': 'Entwickeln Sie zukunftsweisende ML-Modelle in unserem Data Science Team...',
            'firmenname': 'DataDriven Systems'
        },
        {
            'titel': 'Head of AI & Automation (m/w/d)',
            'quelle': 'StepStone',
            'quelle_url': 'https://www.stepstone.de/stellenangebote--Head-AI-Automation-Düsseldorf',
            'keywords': 'AI,Automation,Leadership,Digital Transformation',
            'textvorschau': 'Führen Sie unser AI-Team und gestalten Sie die digitale Zukunft...',
            'firmenname': 'Enterprise Tech AG'
        },
        {
            'titel': 'Prompt Engineer - Generative AI Applications',
            'quelle': 'StepStone',
            'quelle_url': 'https://www.stepstone.de/stellenangebote--Prompt-Engineer-Köln',
            'keywords': 'Prompt Engineering,GenAI,NLP,LLM',
            'textvorschau': 'Als Prompt Engineer optimieren Sie unsere KI-gestützten Anwendungen...',
            'firmenname': 'AI Startup Hub'
        },
        {
            'titel': 'Data Scientist - Copilot & AI Assistant Development',
            'quelle': 'StepStone',
            'quelle_url': 'https://www.stepstone.de/stellenangebote--Data-Scientist-Stuttgart',
            'keywords': 'Copilot,AI Assistant,Data Science,Python',
            'textvorschau': 'Unterstützen Sie unser Team bei der Entwicklung intelligenter Assistenten...',
            'firmenname': 'SmartWork Solutions'
        },
        {
            'titel': 'AI Solutions Architect (m/w/d) - Enterprise',
            'quelle': 'StepStone',
            'quelle_url': 'https://www.stepstone.de/stellenangebote--AI-Solutions-Architect-Leipzig',
            'keywords': 'AI,Solutions Architect,Enterprise,Cloud',
            'textvorschau': 'Designen Sie skalierbare KI-Lösungen für Großunternehmen...',
            'firmenname': 'CloudFirst GmbH'
        }
    ]

    for lead_data in demo_leads:
        # Check if lead already exists
        existing = Lead.query.filter_by(titel=lead_data['titel']).first()
        if not existing:
            lead = Lead(
                titel=lead_data['titel'],
                quelle=lead_data['quelle'],
                quelle_url=lead_data['quelle_url'],
                keywords=lead_data['keywords'],
                textvorschau=lead_data['textvorschau'],
                firmenname=lead_data['firmenname'],
                status=LeadStatus.NEU.value
            )
            db.session.add(lead)

    db.session.commit()

    return jsonify({'message': f'Demo-Daten erfolgreich geladen', 'count': len(demo_leads)})
