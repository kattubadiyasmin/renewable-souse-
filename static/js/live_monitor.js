/**
 * WattWise - Real-Time Campus Simulation & Telemetry Monitor
 */

let lastLiveReading = null;
let streamInterval = null;
let streamCount = 0;

document.addEventListener('DOMContentLoaded', () => {
    // Generate initial reading on page load
    generateLiveReading();

    // Auto-stream toggle listener
    const autoToggle = document.getElementById('live-auto-stream');
    if (autoToggle) {
        autoToggle.addEventListener('change', (e) => {
            if (e.target.checked) {
                showToast('Auto-Stream mode started (3-second interval).', 'info');
                streamInterval = setInterval(() => {
                    generateLiveReading(false); // auto mode don't show toast
                }, 3000);
            } else {
                if (streamInterval) clearInterval(streamInterval);
                showToast('Auto-Stream mode stopped.', 'info');
            }
        });
    }
});

async function generateLiveReading(notify = true) {
    const bldSelect = document.getElementById('live-building-select');
    const anomalyCheckbox = document.getElementById('live-simulate-anomaly');
    const genBtn = document.getElementById('gen-live-btn');

    const building = bldSelect ? bldSelect.value : 'Main Block';
    const forceAnomaly = anomalyCheckbox ? anomalyCheckbox.checked : false;

    const params = new URLSearchParams();
    params.append('building', building);
    if (forceAnomaly) params.append('force_anomaly', 'true');

    try {
        if (genBtn && notify) {
            genBtn.disabled = true;
            genBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Polling Telemetry...';
        }

        const res = await fetch(`/api/live?${params.toString()}`);
        const json = await res.json();

        if (json.status !== 'success') {
            showToast(json.message || 'Error polling live telemetry.', 'error');
            return;
        }

        const reading = json.data;
        lastLiveReading = reading;

        updateLiveGauges(reading);
        appendStreamRow(reading);

        if (notify) {
            showToast(`Telemetry updated for ${reading.building_name}`, 'info');
        }

    } catch (err) {
        console.error(err);
        showToast('Failed to poll live sensor data.', 'error');
    } finally {
        if (genBtn && notify) {
            genBtn.disabled = false;
            genBtn.innerHTML = '<i class="fas fa-bolt"></i> <span>Generate Live Reading</span>';
        }
    }
}

function updateLiveGauges(r) {
    document.getElementById('live-cons').innerHTML = `${r.energy_consumption} <span class="kpi-unit">kWh</span>`;
    document.getElementById('live-solar-gen').innerHTML = `${r.solar_generated} <span class="kpi-unit">kWh</span>`;
    document.getElementById('live-solar-used').innerHTML = `${r.solar_used} <span class="kpi-unit">kWh</span>`;
    document.getElementById('live-battery').innerHTML = `${r.battery_level} <span class="kpi-unit">%</span>`;
    document.getElementById('live-temp').innerHTML = `${r.temperature} <span class="kpi-unit">°C</span>`;
    document.getElementById('live-weather').textContent = r.weather_condition;
    document.getElementById('live-timestamp').textContent = r.timestamp;

    // Battery styling alert
    const battCard = document.getElementById('live-batt-card');
    const battSub = document.getElementById('live-batt-sub');
    if (r.battery_level < 20.0) {
        battCard.className = 'kpi-card danger';
        battSub.innerHTML = '<i class="fas fa-triangle-exclamation"></i> Critical Low Storage!';
    } else {
        battCard.className = 'kpi-card';
        battSub.innerHTML = '<i class="fas fa-battery-half"></i> Storage State';
    }

    // Weather icon update
    const weatherIcon = document.getElementById('live-weather-icon');
    if (weatherIcon) {
        let iconClass = 'fa-sun';
        if (r.weather_condition === 'Partly Cloudy') iconClass = 'fa-cloud-sun';
        else if (r.weather_condition === 'Cloudy') iconClass = 'fa-cloud';
        else if (r.weather_condition === 'Rainy') iconClass = 'fa-cloud-showers-heavy';
        weatherIcon.innerHTML = `<i class="fas ${iconClass}"></i>`;
    }

    // Anomaly Banner Display
    const anomalyBox = document.getElementById('live-anomaly-alert');
    const anomalyMsg = document.getElementById('live-anomaly-msg');
    if (r.is_anomaly) {
        anomalyBox.style.display = 'block';
        anomalyMsg.textContent = r.anomaly_message || 'Unusual energy spike detected outside normal bounds.';
    } else {
        anomalyBox.style.display = 'none';
    }
}

function appendStreamRow(r) {
    const tbody = document.getElementById('live-stream-body');
    if (!tbody) return;

    // Remove placeholder if present
    if (streamCount === 0) {
        tbody.innerHTML = '';
    }

    streamCount++;
    document.getElementById('stream-count-badge').textContent = `${streamCount} Readings Logged`;

    const row = document.createElement('tr');
    if (r.is_anomaly) {
        row.style.backgroundColor = 'rgba(239, 68, 68, 0.12)';
    }

    const statusBadge = r.is_anomaly
        ? '<span class="badge badge-high"><i class="fas fa-triangle-exclamation"></i> ANOMALY</span>'
        : '<span class="badge badge-success"><i class="fas fa-check"></i> NORMAL</span>';

    row.innerHTML = `
        <td style="color: var(--text-dim); font-size: 0.82rem;">${r.time}</td>
        <td style="font-weight: 600;">${r.building_name}</td>
        <td style="color: var(--cyan); font-weight: 600;">${r.energy_consumption}</td>
        <td style="color: var(--solar);">${r.solar_generated}</td>
        <td>${r.solar_used}</td>
        <td>${r.battery_level}%</td>
        <td>${r.temperature}</td>
        <td>${r.weather_condition}</td>
        <td>${statusBadge}</td>
    `;

    tbody.insertBefore(row, tbody.firstChild);

    // Keep table capped at 30 rows in DOM
    if (tbody.children.length > 30) {
        tbody.removeChild(tbody.lastChild);
    }
}

async function saveCurrentLiveReading() {
    if (!lastLiveReading) {
        showToast('No live reading generated yet.', 'error');
        return;
    }

    const saveBtn = document.getElementById('save-live-btn');

    try {
        if (saveBtn) {
            saveBtn.disabled = true;
            saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
        }

        const res = await fetch('/api/live/save', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(lastLiveReading)
        });

        const json = await res.json();

        if (res.ok && json.status === 'success') {
            showToast(json.message || 'Live reading successfully committed to SQLite database.', 'success');
        } else {
            showToast(json.message || 'Error saving reading.', 'error');
        }

    } catch (err) {
        console.error(err);
        showToast('Failed to connect to database.', 'error');
    } finally {
        if (saveBtn) {
            saveBtn.disabled = false;
            saveBtn.innerHTML = '<i class="fas fa-floppy-disk"></i> <span>Save to Database</span>';
        }
    }
}
