// FunnyFunnel - Lead Generator App (2025 Edition)

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

    // Close modal on outside click or Escape
    document.getElementById('letterModal').addEventListener('click', (e) => {
        if (e.target.id === 'letterModal') closeModal();
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeModal();
    });
}

// API Calls with loading state
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
        leadListEl.innerHTML = '<div class="loading" id="loading">Leads werden geladen...</div>';

        const statusFilter = document.getElementById('statusFilter').value;
        const keywordFilter = document.getElementById('keywordFilter').value;

        let queryParams = new URLSearchParams();
        if (statusFilter) queryParams.append('status', statusFilter);
        if (keywordFilter) queryParams.append('keyword', keywordFilter);

        const queryString = queryParams.toString();
        leads = await apiCall(`/leads${queryString ? '?' + queryString : ''}`);

        renderLeads();
        updateStats();
    } catch (error) {
        leadListEl.innerHTML = `
            <div class="empty-state">
                <h3>Fehler beim Laden</h3>
                <p>${escapeHtml(error.message)}</p>
            </div>
        `;
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
                <p>Klicken Sie auf "Demo-Daten" um Beispieldaten zu erstellen.</p>
            </div>
        `;
        return;
    }

    leadListEl.innerHTML = leads.map((lead, index) => createLeadCard(lead, index)).join('');
}

// Create HTML for a single lead card
function createLeadCard(lead, index) {
    const keywords = (lead.keywords || []).slice(0, 4);
    const keywordTags = keywords.map(k => `<span class="keyword-tag">${escapeHtml(k)}</span>`).join('');

    const isActivated = lead.status !== 'neu';
    const canResearch = lead.status === 'aktiviert';
    const canGenerateLetter = ['recherchiert', 'anschreiben_erstellt', 'angeschrieben', 'antwort_erhalten'].includes(lead.status);

    return `
        <div class="lead-card" id="lead-${lead.id}" style="animation-delay: ${Math.min(index * 0.05, 0.3)}s">
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
    // Use volltext if available, otherwise use textvorschau
    const jobText = lead.volltext || lead.textvorschau || 'Keine Beschreibung verfügbar';

    return `
        <div class="detail-section">
            <h4><span>📄</span> Jobanzeige</h4>
            <div class="fulltext-box">${escapeHtml(jobText).replace(/\n/g, '<br>')}</div>
            ${lead.quelle_url ? `
                <p style="margin-top: 12px;">
                    <a href="${escapeHtml(lead.quelle_url)}" target="_blank" rel="noopener">
                        Zur Originalanzeige auf ${escapeHtml(lead.quelle)} →
                    </a>
                </p>
            ` : ''}
        </div>

        <div class="detail-section">
            <h4><span>🏢</span> Firmendaten</h4>
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

        <div class="detail-section">
            <h4><span>👤</span> Ansprechpartner</h4>
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

        ${lead.anschreiben ? `
            <div class="detail-section">
                <h4><span>✉️</span> Anschreiben</h4>
                <div class="letter-box">${escapeHtml(lead.anschreiben)}</div>
            </div>
        ` : ''}

        <div class="lead-actions">
            ${canResearch ? `
                <button class="btn btn-primary" onclick="event.stopPropagation(); researchLead(${lead.id}, this)">
                    <span>🔍</span> Recherchieren
                </button>
            ` : ''}
            ${canGenerateLetter ? `
                <button class="btn btn-success" onclick="event.stopPropagation(); openLetterModal(${lead.id})">
                    <span>✉️</span> ${lead.anschreiben ? 'Anschreiben bearbeiten' : 'Anschreiben erstellen'}
                </button>
            ` : ''}
            <select class="status-select" onchange="updateStatus(${lead.id}, this.value)" onclick="event.stopPropagation()">
                ${Object.entries(STATUS_LABELS).map(([value, label]) =>
                    `<option value="${value}" ${lead.status === value ? 'selected' : ''}>${label}</option>`
                ).join('')}
            </select>
            <button class="btn btn-outline btn-small" onclick="event.stopPropagation(); deleteLead(${lead.id})">
                <span>🗑️</span> Löschen
            </button>
        </div>
    `;
}

// Toggle lead card expansion
function toggleLead(leadId) {
    const card = document.getElementById(`lead-${leadId}`);
    const wasExpanded = card.classList.contains('expanded');

    // Close all other cards
    document.querySelectorAll('.lead-card.expanded').forEach(c => {
        if (c.id !== `lead-${leadId}`) {
            c.classList.remove('expanded');
        }
    });

    card.classList.toggle('expanded');
}

// Activate a lead (checkbox click)
async function activateLead(leadId) {
    try {
        await apiCall(`/leads/${leadId}/activate`, 'POST');
        showToast('Lead aktiviert', 'success');
        loadLeads();
    } catch (error) {
        showToast(error.message, 'error');
    }
}

// Research a lead
async function researchLead(leadId, btn) {
    const originalContent = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span>⏳</span> Recherchiere...';

    try {
        await apiCall(`/leads/${leadId}/research`, 'POST');
        showToast('Recherche abgeschlossen', 'success');
        loadLeads();
    } catch (error) {
        showToast(error.message, 'error');
        btn.innerHTML = originalContent;
        btn.disabled = false;
    }
}

// Open letter modal
async function openLetterModal(leadId) {
    currentLeadId = leadId;
    const lead = leads.find(l => l.id === leadId);

    if (!lead.anschreiben) {
        try {
            showToast('Generiere Anschreiben...', 'info');
            const updatedLead = await apiCall(`/leads/${leadId}/generate-letter`, 'POST');
            lead.anschreiben = updatedLead.anschreiben;
        } catch (error) {
            showToast(error.message, 'error');
            return;
        }
    }

    document.getElementById('letterText').value = lead.anschreiben || '';
    document.getElementById('letterModal').classList.add('active');
    document.getElementById('letterText').focus();
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
        showToast('Status aktualisiert', 'success');
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
        showToast('Lead gelöscht', 'success');
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

        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = 'leads_export.csv';
        if (contentDisposition) {
            const match = contentDisposition.match(/filename=(.+)/);
            if (match) filename = match[1];
        }

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
    const btn = document.getElementById('loadDemoData');
    const originalContent = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span>⏳</span> Lade...';

    try {
        await apiCall('/seed-demo', 'POST');
        showToast('Demo-Daten geladen', 'success');
        loadLeads();
    } catch (error) {
        showToast(error.message, 'error');
    } finally {
        btn.innerHTML = originalContent;
        btn.disabled = false;
    }
}

// Animate number counting
function animateValue(element, start, end, duration) {
    const range = end - start;
    const startTime = performance.now();

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const easeOut = 1 - Math.pow(1 - progress, 3);
        const current = Math.round(start + range * easeOut);
        element.textContent = current;

        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }

    requestAnimationFrame(update);
}

// Update statistics with animation
function updateStats() {
    const stats = {
        total: leads.length,
        neu: leads.filter(l => l.status === 'neu').length,
        aktiviert: leads.filter(l => l.status === 'aktiviert').length,
        recherchiert: leads.filter(l => l.status === 'recherchiert').length,
        anschreiben: leads.filter(l => ['anschreiben_erstellt', 'angeschrieben', 'antwort_erhalten'].includes(l.status)).length
    };

    const elements = {
        total: document.getElementById('statTotal'),
        neu: document.getElementById('statNeu'),
        aktiviert: document.getElementById('statAktiviert'),
        recherchiert: document.getElementById('statRecherchiert'),
        anschreiben: document.getElementById('statAnschreiben')
    };

    Object.entries(stats).forEach(([key, value]) => {
        const el = elements[key];
        const current = parseInt(el.textContent) || 0;
        if (current !== value) {
            animateValue(el, current, value, 500);
        }
    });
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

// ==================== StepStone Import Functions ====================

let searchResults = [];
let selectedJobs = new Set();

// Setup import modal event listeners
function setupImportEventListeners() {
    document.getElementById('openImportModal')?.addEventListener('click', openImportModal);
    document.getElementById('searchStepStone')?.addEventListener('click', searchStepStone);
    document.getElementById('selectAllResults')?.addEventListener('click', selectAllResults);
    document.getElementById('deselectAllResults')?.addEventListener('click', deselectAllResults);
    document.getElementById('importSelected')?.addEventListener('click', importSelectedJobs);

    // Close import modal on outside click
    document.getElementById('importModal')?.addEventListener('click', (e) => {
        if (e.target.id === 'importModal') closeImportModal();
    });
}

// Call this in DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
    setupImportEventListeners();
});

// Open import modal
function openImportModal() {
    document.getElementById('importModal').classList.add('active');
    // Reset state
    searchResults = [];
    selectedJobs.clear();
    document.getElementById('searchResults').style.display = 'none';
    document.getElementById('searchLoading').style.display = 'none';
    updateImportButton();
}

// Close import modal
function closeImportModal() {
    document.getElementById('importModal').classList.remove('active');
}

// Search StepStone
async function searchStepStone() {
    const btn = document.getElementById('searchStepStone');
    const originalContent = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span>⏳</span> Suche läuft...';

    // Show loading, hide results
    document.getElementById('searchLoading').style.display = 'block';
    document.getElementById('searchResults').style.display = 'none';

    // Get search parameters
    const searchParams = {
        keywords: document.getElementById('searchKeywords').value || 'KI AI GenAI Copilot',
        location: document.getElementById('searchLocation').value || null,
        radius: parseInt(document.getElementById('searchRadius').value) || 30,
        date_filter: document.getElementById('searchDateFilter').value || null,
        job_title_filter: document.getElementById('searchJobTitle').value || null,
        max_results: parseInt(document.getElementById('searchMaxResults').value) || 10
    };

    try {
        const response = await apiCall('/stepstone/search', 'POST', searchParams);

        document.getElementById('searchLoading').style.display = 'none';

        if (response.success && response.jobs.length > 0) {
            searchResults = response.jobs;
            selectedJobs.clear();
            renderSearchResults();
            document.getElementById('searchResults').style.display = 'block';
            showToast(`${response.count} Jobs gefunden`, 'success');
        } else {
            document.getElementById('searchResults').style.display = 'block';
            document.getElementById('resultsList').innerHTML = `
                <div class="empty-results">
                    <h4>Keine Ergebnisse</h4>
                    <p>Versuchen Sie andere Suchbegriffe oder erweitern Sie den Suchbereich.</p>
                </div>
            `;
            document.getElementById('resultsCount').textContent = '0 Ergebnisse gefunden';
            searchResults = [];
        }
    } catch (error) {
        document.getElementById('searchLoading').style.display = 'none';
        showToast('Fehler bei der Suche: ' + error.message, 'error');
        console.error(error);
    } finally {
        btn.innerHTML = originalContent;
        btn.disabled = false;
    }
}

// Render search results
function renderSearchResults() {
    const listEl = document.getElementById('resultsList');
    document.getElementById('resultsCount').textContent = `${searchResults.length} Ergebnisse gefunden`;

    listEl.innerHTML = searchResults.map((job, index) => {
        const keywords = (job.keywords || []).slice(0, 3);
        const keywordTags = keywords.map(k => `<span class="keyword-tag">${escapeHtml(k)}</span>`).join('');

        return `
            <div class="result-item ${selectedJobs.has(index) ? 'selected' : ''}"
                 onclick="toggleJobSelection(${index})">
                <input type="checkbox" class="result-checkbox"
                       ${selectedJobs.has(index) ? 'checked' : ''}
                       onclick="event.stopPropagation(); toggleJobSelection(${index})">
                <div class="result-content">
                    <div class="result-title">${escapeHtml(job.titel)}</div>
                    <div class="result-meta">
                        ${job.firmenname ? `<span class="result-company">🏢 ${escapeHtml(job.firmenname)}</span>` : ''}
                        ${job.standort ? `<span class="result-location">📍 ${escapeHtml(job.standort)}</span>` : ''}
                    </div>
                    ${job.textvorschau ? `<div class="result-preview">${escapeHtml(job.textvorschau)}</div>` : ''}
                    ${keywordTags ? `<div class="result-keywords">${keywordTags}</div>` : ''}
                </div>
            </div>
        `;
    }).join('');

    updateImportButton();
}

// Toggle job selection
function toggleJobSelection(index) {
    if (selectedJobs.has(index)) {
        selectedJobs.delete(index);
    } else {
        selectedJobs.add(index);
    }
    renderSearchResults();
}

// Select all results
function selectAllResults() {
    searchResults.forEach((_, index) => selectedJobs.add(index));
    renderSearchResults();
}

// Deselect all results
function deselectAllResults() {
    selectedJobs.clear();
    renderSearchResults();
}

// Update import button state
function updateImportButton() {
    const btn = document.getElementById('importSelected');
    const countEl = document.getElementById('importCount');
    const count = selectedJobs.size;

    countEl.textContent = count;
    btn.disabled = count === 0;
}

// Import selected jobs
async function importSelectedJobs() {
    if (selectedJobs.size === 0) return;

    const btn = document.getElementById('importSelected');
    const originalContent = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span>⏳</span> Importiere...';

    // Get selected jobs
    const jobsToImport = Array.from(selectedJobs).map(index => searchResults[index]);

    try {
        const response = await apiCall('/stepstone/import', 'POST', { jobs: jobsToImport });

        if (response.success) {
            showToast(response.message, 'success');
            closeImportModal();
            loadLeads(); // Refresh lead list
        } else {
            showToast('Import fehlgeschlagen', 'error');
        }
    } catch (error) {
        showToast('Fehler beim Import: ' + error.message, 'error');
        console.error(error);
    } finally {
        btn.innerHTML = originalContent;
        btn.disabled = selectedJobs.size === 0;
    }
}

// Make functions globally available for onclick handlers
window.toggleJobSelection = toggleJobSelection;
window.openImportModal = openImportModal;
window.closeImportModal = closeImportModal;
window.selectAllResults = selectAllResults;
window.deselectAllResults = deselectAllResults;
