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
    Research company information for a lead using Perplexity AI.
    Finds real company data: website, address, email, and decision makers.
    """
    from app.perplexity import PerplexityService

    lead = Lead.query.get_or_404(lead_id)

    try:
        perplexity = PerplexityService()

        # Research company information
        research_result = perplexity.research_company(
            company_name=lead.firmenname or "Unbekannt",
            job_title=lead.titel,
            location=lead.standort
        )

        # Update lead with researched data (only if we found something)
        if research_result.get('firmen_website'):
            lead.firmen_website = research_result['firmen_website']
        if research_result.get('firmen_adresse'):
            lead.firmen_adresse = research_result['firmen_adresse']
        if research_result.get('firmen_email'):
            lead.firmen_email = research_result['firmen_email']
        if research_result.get('ansprechpartner_name'):
            lead.ansprechpartner_name = research_result['ansprechpartner_name']
        if research_result.get('ansprechpartner_rolle'):
            lead.ansprechpartner_rolle = research_result['ansprechpartner_rolle']
        if research_result.get('ansprechpartner_linkedin'):
            lead.ansprechpartner_linkedin = research_result['ansprechpartner_linkedin']
            lead.ansprechpartner_quelle = 'LinkedIn (via Perplexity)'

        # Update status to recherchiert
        lead.status = LeadStatus.RECHERCHIERT.value
        db.session.commit()

        return jsonify(lead.to_dict())

    except ValueError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        print(f"Research error for lead {lead_id}: {e}")
        return jsonify({'error': f'Recherche fehlgeschlagen: {str(e)}'}), 500


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


@api_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get lead statistics by status."""
    from sqlalchemy import func

    # Get counts per status
    status_counts = db.session.query(
        Lead.status, func.count(Lead.id)
    ).group_by(Lead.status).all()

    # Build stats dict
    stats = {
        'total': Lead.query.count(),
        'neu': 0,
        'aktiviert': 0,
        'recherchiert': 0,
        'anschreiben_erstellt': 0,
        'angeschrieben': 0,
        'antwort_erhalten': 0
    }

    for status, count in status_counts:
        if status in stats:
            stats[status] = count

    # Combined anschreiben count
    stats['anschreiben'] = (
        stats['anschreiben_erstellt'] +
        stats['angeschrieben'] +
        stats['antwort_erhalten']
    )

    return jsonify(stats)


# ==================== StepStone Import API ====================

@api_bp.route('/stepstone/search', methods=['POST'])
def search_stepstone():
    """
    Search StepStone for job listings.

    Request body:
    {
        "keywords": "AI Engineer",
        "location": "Berlin",
        "radius": 30,
        "date_filter": 7,
        "job_title_filter": "Engineer",
        "max_pages": 2
    }
    """
    from app.stepstone import stepstone_service

    data = request.json or {}

    keywords = data.get('keywords', 'KI AI GenAI Copilot')
    location = data.get('location')
    radius = data.get('radius', 30)
    date_filter = data.get('date_filter')  # 1, 3, 7, 14, 30 days
    job_title_filter = data.get('job_title_filter')
    max_pages = min(data.get('max_pages', 1), 3)  # Limit to 3 pages
    max_results = data.get('max_results', 10)  # Default to 10 results

    try:
        jobs = stepstone_service.search_jobs(
            keywords=keywords,
            location=location,
            radius=radius,
            max_pages=max_pages,
            date_filter=date_filter,
            job_title_filter=job_title_filter
        )

        # Limit results to requested amount (default 10)
        jobs = jobs[:max_results]

        return jsonify({
            'success': True,
            'count': len(jobs),
            'jobs': jobs
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'jobs': []
        }), 500


@api_bp.route('/stepstone/import', methods=['POST'])
def import_stepstone_jobs():
    """
    Import selected jobs from StepStone search results as leads.

    Request body:
    {
        "jobs": [
            {
                "titel": "...",
                "firmenname": "...",
                "quelle_url": "...",
                ...
            }
        ]
    }
    """
    data = request.json or {}
    jobs = data.get('jobs', [])

    if not jobs:
        return jsonify({'error': 'Keine Jobs zum Importieren'}), 400

    imported = 0
    skipped = 0

    for job in jobs:
        # Check if already exists by URL
        if job.get('quelle_url'):
            existing = Lead.query.filter_by(quelle_url=job['quelle_url']).first()
            if existing:
                skipped += 1
                continue

        # Create new lead
        keywords = job.get('keywords', [])
        if isinstance(keywords, list):
            keywords = ','.join(keywords)

        lead = Lead(
            titel=job.get('titel', 'Unbekannter Titel'),
            quelle=job.get('quelle', 'StepStone'),
            quelle_url=job.get('quelle_url'),
            keywords=keywords,
            textvorschau=job.get('textvorschau'),
            firmenname=job.get('firmenname'),
            status=LeadStatus.NEU.value
        )

        db.session.add(lead)
        imported += 1

    db.session.commit()

    return jsonify({
        'success': True,
        'imported': imported,
        'skipped': skipped,
        'message': f'{imported} Leads importiert, {skipped} übersprungen (bereits vorhanden)'
    })


@api_bp.route('/stepstone/regions', methods=['GET'])
def get_stepstone_regions():
    """Get available German regions for filtering."""
    from app.stepstone import StepStoneService
    return jsonify(StepStoneService.get_regions())


@api_bp.route('/stepstone/keywords', methods=['GET'])
def get_ai_keywords():
    """Get predefined AI-related keywords."""
    from app.stepstone import StepStoneService
    return jsonify(StepStoneService.get_ai_keywords())
