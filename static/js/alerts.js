/**
 * WattWise - Wastage Detection & Anomaly Alerts Logic
 */

let allAlerts = [];
let currentFilter = 'ALL';

document.addEventListener('DOMContentLoaded', () => {
    loadAlerts();
});

async function loadAlerts() {
    const tbody = document.getElementById('alerts-table-body');
    if (tbody) {
        tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: var(--text-dim);"><i class="fas fa-spinner fa-spin"></i> Scanning historical telemetry & running Isolation Forest...</td></tr>';
    }

    try {
        const res = await fetch('/api/alerts?limit=150');
        const json = await res.json();

        if (json.status !== 'success') {
            showToast(json.message || 'Error running anomaly detection.', 'error');
            return;
        }

        const data = json.data;
        allAlerts = data.alerts || [];

        // Update Summary Counters
        document.getElementById('alert-total-count').textContent = data.summary.total_alerts;
        document.getElementById('alert-high-count').textContent = data.summary.high;
        document.getElementById('alert-med-count').textContent = data.summary.medium;
        document.getElementById('alert-low-count').textContent = data.summary.low;

        // ML Badge
        const mlBadge = document.getElementById('ml-engine-badge');
        if (mlBadge) {
            if (data.ml_active) {
                mlBadge.className = 'badge badge-success';
                mlBadge.innerHTML = '<i class="fas fa-check"></i> Isolation Forest ML Active';
            } else {
                mlBadge.className = 'badge badge-medium';
                mlBadge.innerHTML = '<i class="fas fa-info-circle"></i> Rule Engine Fallback Active';
            }
        }

        renderFilteredAlerts();

    } catch (err) {
        console.error(err);
        showToast('Failed to fetch anomaly alerts.', 'error');
    }
}

function filterAlerts(severity) {
    currentFilter = severity;

    // Update active tab styles
    document.querySelectorAll('.filter-tab').forEach(btn => {
        if (btn.getAttribute('data-filter') === severity) {
            btn.classList.add('active');
            btn.style.backgroundColor = 'var(--primary)';
            btn.style.color = '#ffffff';
        } else {
            btn.classList.remove('active');
            btn.style.backgroundColor = 'var(--bg-card-hover)';
            btn.style.color = 'var(--text-main)';
        }
    });

    renderFilteredAlerts();
}

function renderFilteredAlerts() {
    const tbody = document.getElementById('alerts-table-body');
    if (!tbody) return;

    let filtered = allAlerts;
    if (currentFilter !== 'ALL') {
        filtered = allAlerts.filter(a => a.severity === currentFilter);
    }

    if (!filtered || filtered.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-dim); padding: 24px;">No ${currentFilter.toLowerCase()} priority anomalies detected.</td></tr>`;
        return;
    }

    tbody.innerHTML = filtered.map(a => {
        let badgeClass = 'badge-low';
        if (a.severity === 'HIGH') badgeClass = 'badge-high';
        else if (a.severity === 'MEDIUM') badgeClass = 'badge-medium';

        let methodBadge = a.detection_method.includes('IsolationForest') 
            ? '<span class="card-badge" style="color:#a78bfa; border:1px solid rgba(167,139,250,0.3);"><i class="fas fa-brain"></i> ML Model</span>'
            : '<span class="card-badge"><i class="fas fa-sliders"></i> Rule Engine</span>';

        return `
            <tr>
                <td style="font-weight: 600;">${a.building}</td>
                <td style="color: var(--text-dim); font-size: 0.8rem;">
                    <div>${a.date}</div>
                    <div style="color: var(--text-main); font-weight: 500;">${a.time}</div>
                </td>
                <td><span class="badge ${badgeClass}">${a.severity}</span></td>
                <td style="font-weight: 600; color: #f8fafc;">${a.issue}</td>
                <td style="font-size: 0.82rem; color: var(--text-muted); line-height: 1.4;">${a.reason}</td>
                <td style="font-size: 0.82rem; color: #6ee7b7; line-height: 1.4;">
                    <i class="fas fa-wrench" style="margin-right: 4px;"></i> ${a.recommendation}
                </td>
                <td>${methodBadge}</td>
            </tr>
        `;
    }).join('');
}
