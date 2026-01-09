from app import db
from datetime import datetime
from enum import Enum

class LeadStatus(str, Enum):
    NEU = 'neu'
    AKTIVIERT = 'aktiviert'
    RECHERCHIERT = 'recherchiert'
    ANSCHREIBEN_ERSTELLT = 'anschreiben_erstellt'
    ANGESCHRIEBEN = 'angeschrieben'
    ANTWORT_ERHALTEN = 'antwort_erhalten'

class Lead(db.Model):
    __tablename__ = 'leads'

    id = db.Column(db.Integer, primary_key=True)

    # Job posting data
    titel = db.Column(db.String(500), nullable=False)
    quelle = db.Column(db.String(200), default='StepStone')
    quelle_url = db.Column(db.String(1000))
    keywords = db.Column(db.String(500))  # Comma-separated
    textvorschau = db.Column(db.Text)  # Full job description text
    volltext = db.Column(db.Text)

    # Company data
    firmenname = db.Column(db.String(300))
    firmen_website = db.Column(db.String(500))
    firmen_adresse = db.Column(db.String(500))
    firmen_email = db.Column(db.String(200))

    # Contact person data
    ansprechpartner_name = db.Column(db.String(200))
    ansprechpartner_rolle = db.Column(db.String(200))
    ansprechpartner_linkedin = db.Column(db.String(500))
    ansprechpartner_quelle = db.Column(db.String(100))

    # Cover letter
    anschreiben = db.Column(db.Text)

    # Status and metadata
    status = db.Column(db.String(50), default=LeadStatus.NEU.value)
    erstellt_am = db.Column(db.DateTime, default=datetime.utcnow)
    aktualisiert_am = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'titel': self.titel,
            'quelle': self.quelle,
            'quelle_url': self.quelle_url,
            'keywords': self.keywords.split(',') if self.keywords else [],
            'textvorschau': self.textvorschau,
            'volltext': self.volltext,
            'firmenname': self.firmenname,
            'firmen_website': self.firmen_website,
            'firmen_adresse': self.firmen_adresse,
            'firmen_email': self.firmen_email,
            'ansprechpartner_name': self.ansprechpartner_name,
            'ansprechpartner_rolle': self.ansprechpartner_rolle,
            'ansprechpartner_linkedin': self.ansprechpartner_linkedin,
            'ansprechpartner_quelle': self.ansprechpartner_quelle,
            'anschreiben': self.anschreiben,
            'status': self.status,
            'erstellt_am': self.erstellt_am.isoformat() if self.erstellt_am else None,
            'aktualisiert_am': self.aktualisiert_am.isoformat() if self.aktualisiert_am else None
        }

    @staticmethod
    def get_status_options():
        return [status.value for status in LeadStatus]
