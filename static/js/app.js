// FunnyFunnel - Lead Generator App

const API_BASE = '/api';
let leads = [];
let currentLeadId = null;

// Status labels in German
const STATUS_LABELS = {
    'neu': 'Neu',
    'aktiviert': 'Aktiviert',
    'recherchiert': 'Recherchiert',
    'anschreiben_erstellt': 'Anschreiben erstellt',
    'angeschrieben': 'Angeschrieben',
    'antwort_erhalten': 'Antwort erhalten'
};

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    loadLeads();
    setupEventListeners();
});

// Setup event listeners
function setupEventListeners() {
    document.getElementById('applyFilters').addEventListener('click', loadLeads);
    document.getElementById('exportCSV').addEventListener('click', exportCSV);
    document.getElementById('loadDemoData').addEventListener('click', loadDemoData);

    // Filter on Enter key
    document.getElementById('keywordFilter').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') loadLeads();
    });

    // Close modal on outside click
    document.getElementById('letterModal').addEventListener('click', (e) => {
        if (e.target.id === 'letterModal') closeModal();
    });
}

// API Calls
async function apiCall(endpoint, method = 'GET', data = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json'
        }
    };

    if (data) {
        options.body = JSON.stringify(data);
    }

    const response = await fetch(`${API_BASE}${endpoint}`, options);

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'API Error');
    }

    // Handle CSV export
    if (response.headers.get('Content-Type')?.includes('text/csv')) {
        return response;
    }

    return response.json();
}

// Load leads from API
async function loadLeads() {
    const loadingEl = document.getElementById('loading');
    const leadListEl = document.getElementById('leadList');

    try {
        loadingEl.style.display = 'block';
        leadListEl.innerHTML = '';

        // Build query params
        const statusFilter = document.getElementById('statusFilter').value;
        const keywordFilter = document.getElementById('keywordFilter').value;

        let queryParams = new URLSearchParams();
        if (statusFilter) queryParams.append('status', statusFilter);
        if (keywordFilter) queryParams.append('keyword', keywordFilter);

        const queryString = queryParams.toString();
        leads = await apiCall(`/leads${queryString ? '?' + queryString : ''}`);

        loadingEl.style.display = 'none';
        renderLeads();
        updateStats();
    } catch (error) {
        loadingEl.textContent = 'Fehler beim Laden der Leads';
        console.error(error);
        showToast('Fehler beim Laden der Leads', 'error');
    }
}

// Render leads to DOM
function renderLeads() {
    const leadListEl = document.getElementById('leadList');

    if (leads.length === 0) {
        leadListEl.innerHTML = `
            <div class="empty-state">
                <h3>Keine Leads gefunden</h3>
                <p>Klicken Sie auf "Demo-Daten laden" um Beispieldaten zu erstellen.</p>
            </div>
        `;
        return;
    }

    leadListEl.innerHTML = leads.map(lead => createLeadCard(lead)).join('');
}

// Create HTML for a single lead card
function createLeadCard(lead) {
    const keywords = (lead.keywords || []).slice(0, 4);
    const keywordTags = keywords.map(k => `<span class="keyword-tag">${k}</span>`).join('');

    const isActivated = lead.status !== 'neu';
    const canResearch = lead.status === 'aktiviert';
    const canGenerateLetter = ['recherchiert', 'anschreiben_erstellt', 'angeschrieben', 'antwort_erhalten'].includes(lead.status);

    return `
        <div class="lead-card" id="lead-${lead.id}">
            <div class="lead-header" onclick="toggleLead(${lead.id})">
                <input type="checkbox" class="lead-checkbox"
                    ${isActivated ? 'checked disabled' : ''}
                    onclick="event.stopPropagation(); activateLead(${lead.id})"
                    title="${isActivated ? 'Bereits aktiviert' : 'Klicken zum Aktivieren'}">
                <span class="lead-title">${escapeHtml(lead.titel)}</span>
                <span class="lead-company">${escapeHtml(lead.firmenname || '-')}</span>
                <div class="lead-keywords">${keywordTags}</div>
                <span class="lead-status status-${lead.status}">${STATUS_LABELS[lead.status]}</span>
                <span class="lead-expand">▼</span>
            </div>
            <div class="lead-details">
                ${renderLeadDetails(lead, canResearch, canGenerateLetter)}
            </div>
        </div>
    `;
}

// Render lead details section
function renderLeadDetails(lead, canResearch, canGenerateLetter) {
    return `
        <!-- Preview/Full Text -->
        <div class="detail-section">
            <h4>📄 Jobanzeige</h4>
            ${lead.volltext ? `
                <div class="fulltext-box">${escapeHtml(lead.volltext)}</div>
            ` : `
                <div class="detail-item">
                    <span class="detail-label">Vorschau</span>
                    <span class="detail-value">${escapeHtml(lead.textvorschau || 'Keine Vorschau verfügbar')}</span>
                </div>
            `}
            ${lead.quelle_url ? `
                <p style="margin-top: 10px;">
                    <a href="${escapeHtml(lead.quelle_url)}" target="_blank" rel="noopener">
                        Zur Originalanzeige auf ${escapeHtml(lead.quelle)} →
                    </a>
                </p>
            ` : ''}
        </div>

        <!-- Company Data -->
        <div class="detail-section">
            <h4>🏢 Firmendaten</h4>
            <div class="detail-grid">
                <div class="detail-item">
                    <span class="detail-label">Firmenname</span>
                    <span class="detail-value">${escapeHtml(lead.firmenname || '-')}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Website</span>
                    <span class="detail-value">
                        ${lead.firmen_website ?
                            `<a href="${escapeHtml(lead.firmen_website)}" target="_blank">${escapeHtml(lead.firmen_website)}</a>` :
                            '-'}
                    </span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Adresse</span>
                    <span class="detail-value">${escapeHtml(lead.firmen_adresse || '-')}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">E-Mail</span>
                    <span class="detail-value">
                        ${lead.firmen_email ?
                            `<a href="mailto:${escapeHtml(lead.firmen_email)}">${escapeHtml(lead.firmen_email)}</a>` :
                            '-'}
                    </span>
                </div>
            </div>
        </div>

        <!-- Contact Person -->
        <div class="detail-section">
            <h4>👤 Ansprechpartner</h4>
            <div class="detail-grid">
                <div class="detail-item">
                    <span class="detail-label">Name</span>
                    <span class="detail-value">${escapeHtml(lead.ansprechpartner_name || '-')}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Rolle</span>
                    <span class="detail-value">${escapeHtml(lead.ansprechpartner_rolle || '-')}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">LinkedIn</span>
                    <span class="detail-value">
                        ${lead.ansprechpartner_linkedin ?
                            `<a href="${escapeHtml(lead.ansprechpartner_linkedin)}" target="_blank">Profil öffnen</a>` :
                            '-'}
                    </span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Quelle</span>
                    <span class="detail-value">${escapeHtml(lead.ansprechpartner_quelle || '-')}</span>
                </div>
            </div>
        </div>

        <!-- Cover Letter -->
        ${lead.anschreiben ? `
            <div class="detail-section">
                <h4>✉️ Anschreiben</h4>
                <div class="letter-box">${escapeHtml(lead.anschreiben)}</div>
            </div>
        ` : ''}

        <!-- Actions -->
        <div class="lead-actions">
            ${canResearch ? `
                <button class="btn btn-primary" onclick="researchLead(${lead.id})">
                    🔍 Recherchieren
                </button>
            ` : ''}
            ${canGenerateLetter ? `
                <button class="btn btn-success" onclick="openLetterModal(${lead.id})">
                    ✉️ Anschreiben ${lead.anschreiben ? 'bearbeiten' : 'erstellen'}
                </button>
            ` : ''}
            <select class="status-select" onchange="updateStatus(${lead.id}, this.value)">
                ${Object.entries(STATUS_LABELS).map(([value, label]) =>
                    `<option value="${value}" ${lead.status === value ? 'selected' : ''}>${label}</option>`
                ).join('')}
            </select>
            <button class="btn btn-outline btn-small" onclick="deleteLead(${lead.id})">
                🗑️ Löschen
            </button>
        </div>
    `;
}

// Toggle lead card expansion
function toggleLead(leadId) {
    const card = document.getElementById(`lead-${leadId}`);
    card.classList.toggle('expanded');
}

// Activate a lead (checkbox click)
async function activateLead(leadId) {
    try {
        await apiCall(`/leads/${leadId}/activate`, 'POST');
        showToast('Lead aktiviert - bereit zur Recherche');
        loadLeads();
    } catch (error) {
        showToast(error.message, 'error');
    }
}

// Research a lead
async function researchLead(leadId) {
    const btn = event.target;
    btn.disabled = true;
    btn.textContent = '⏳ Recherchiere...';

    try {
        await apiCall(`/leads/${leadId}/research`, 'POST');
        showToast('Recherche abgeschlossen', 'success');
        loadLeads();
    } catch (error) {
        showToast(error.message, 'error');
    } finally {
        btn.disabled = false;
    }
}

// Open letter modal
async function openLetterModal(leadId) {
    currentLeadId = leadId;
    const lead = leads.find(l => l.id === leadId);

    // If no letter exists yet, generate one first
    if (!lead.anschreiben) {
        try {
            const updatedLead = await apiCall(`/leads/${leadId}/generate-letter`, 'POST');
            lead.anschreiben = updatedLead.anschreiben;
        } catch (error) {
            showToast(error.message, 'error');
            return;
        }
    }

    document.getElementById('letterText').value = lead.anschreiben || '';
    document.getElementById('letterModal').classList.add('active');
}

// Close modal
function closeModal() {
    document.getElementById('letterModal').classList.remove('active');
    currentLeadId = null;
}

// Copy letter to clipboard
async function copyLetter() {
    const letterText = document.getElementById('letterText').value;
    try {
        await navigator.clipboard.writeText(letterText);
        showToast('In Zwischenablage kopiert', 'success');
    } catch (error) {
        // Fallback for older browsers
        const textarea = document.getElementById('letterText');
        textarea.select();
        document.execCommand('copy');
        showToast('In Zwischenablage kopiert', 'success');
    }
}

// Save letter
async function saveLetter() {
    if (!currentLeadId) return;

    const letterText = document.getElementById('letterText').value;

    try {
        await apiCall(`/leads/${currentLeadId}`, 'PUT', {
            anschreiben: letterText,
            status: 'anschreiben_erstellt'
        });
        showToast('Anschreiben gespeichert', 'success');
        closeModal();
        loadLeads();
    } catch (error) {
        showToast(error.message, 'error');
    }
}

// Update lead status
async function updateStatus(leadId, newStatus) {
    try {
        await apiCall(`/leads/${leadId}/status`, 'PUT', { status: newStatus });
        showToast('Status aktualisiert');
        loadLeads();
    } catch (error) {
        showToast(error.message, 'error');
    }
}

// Delete a lead
async function deleteLead(leadId) {
    if (!confirm('Lead wirklich löschen?')) return;

    try {
        await apiCall(`/leads/${leadId}`, 'DELETE');
        showToast('Lead gelöscht');
        loadLeads();
    } catch (error) {
        showToast(error.message, 'error');
    }
}

// Export leads as CSV
async function exportCSV() {
    try {
        const response = await fetch(`${API_BASE}/leads/export`);
        const blob = await response.blob();

        // Get filename from header or generate one
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = 'leads_export.csv';
        if (contentDisposition) {
            const match = contentDisposition.match(/filename=(.+)/);
            if (match) filename = match[1];
        }

        // Download file
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();

        showToast('CSV exportiert', 'success');
    } catch (error) {
        showToast('Export fehlgeschlagen', 'error');
    }
}

// Load demo data
async function loadDemoData() {
    try {
        await apiCall('/seed-demo', 'POST');
        showToast('Demo-Daten geladen', 'success');
        loadLeads();
    } catch (error) {
        showToast(error.message, 'error');
    }
}

// Update statistics
function updateStats() {
    const total = leads.length;
    const neu = leads.filter(l => l.status === 'neu').length;
    const aktiviert = leads.filter(l => l.status === 'aktiviert').length;
    const recherchiert = leads.filter(l => l.status === 'recherchiert').length;
    const anschreiben = leads.filter(l => ['anschreiben_erstellt', 'angeschrieben', 'antwort_erhalten'].includes(l.status)).length;

    document.getElementById('statTotal').textContent = total;
    document.getElementById('statNeu').textContent = neu;
    document.getElementById('statAktiviert').textContent = aktiviert;
    document.getElementById('statRecherchiert').textContent = recherchiert;
    document.getElementById('statAnschreiben').textContent = anschreiben;
}

// Show toast notification
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast show ${type}`;

    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
