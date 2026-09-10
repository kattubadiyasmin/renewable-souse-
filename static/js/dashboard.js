/**
 * WattWise - Dashboard Logic & Live Chart.js Rendering
 */

let consumptionTrendChart = null;
let solarTrendChart = null;
let diurnalChart = null;
let buildingBarChart = null;
let distributionChart = null;

document.addEventListener('DOMContentLoaded', () => {
    loadDashboardData();
});

async function loadDashboardData() {
    const refreshBtn = document.getElementById('refresh-dash-btn');
    if (refreshBtn) {
        refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Refreshing...';
        refreshBtn.disabled = true;
    }

    try {
        const response = await fetch('/api/dashboard');
        const data = await response.json();

        if (data.status !== 'success') {
            showToast(data.message || 'Error loading dashboard telemetry.', 'error');
            return;
        }

        updateKPIs(data.kpis);
        updateInsights(data.insights);
        renderCharts(data.charts);
        renderAlertsTable(data.recent_alerts);

    } catch (err) {
        console.error('Error fetching dashboard data:', err);
        showToast('Failed to fetch dashboard data.', 'error');
    } finally {
        if (refreshBtn) {
            refreshBtn.innerHTML = '<i class="fas fa-arrows-rotate"></i> Refresh Data';
            refreshBtn.disabled = false;
        }
    }
}

function updateKPIs(kpis) {
    if (!kpis) return;

    document.getElementById('kpi-total-cons').innerHTML = `${Number(kpis.total_consumption).toLocaleString()} <span class="kpi-unit">kWh</span>`;
    document.getElementById('kpi-solar-gen').innerHTML = `${Number(kpis.total_solar_generated).toLocaleString()} <span class="kpi-unit">kWh</span>`;
    document.getElementById('kpi-solar-used').innerHTML = `${Number(kpis.total_solar_used).toLocaleString()} <span class="kpi-unit">kWh</span>`;
    document.getElementById('kpi-renewable-pct').innerHTML = `${kpis.renewable_contribution_pct} <span class="kpi-unit">%</span>`;
    document.getElementById('kpi-efficiency-score').innerHTML = `${kpis.efficiency_score} <span class="kpi-unit">/100</span>`;
    document.getElementById('kpi-alerts-count').textContent = kpis.active_wastage_alerts;

    const subtext = document.getElementById('kpi-high-alerts-subtext');
    if (subtext) {
        subtext.innerHTML = `<i class="fas fa-triangle-exclamation"></i> ${kpis.high_severity_alerts} Critical Priority`;
    }
}

function updateInsights(insights) {
    const list = document.getElementById('dashboard-insights-list');
    if (!list) return;

    if (!insights || insights.length === 0) {
        list.innerHTML = '<li class="insight-item">Telemetry data is stable across all buildings.</li>';
        return;
    }

    list.innerHTML = insights.map(item => `
        <li class="insight-item">
            <i class="fas fa-circle-check"></i>
            <span>${item}</span>
        </li>
    `).join('');
}

function renderCharts(charts) {
    if (!charts) return;

    // 1. Energy Consumption Trend Chart
    const daily = charts.daily_trends || [];
    const dailyLabels = daily.map(d => d.date.substring(5)); // MM-DD
    const consData = daily.map(d => d.consumption);
    const solarGenData = daily.map(d => d.solar_generated);

    if (consumptionTrendChart) consumptionTrendChart.destroy();
    consumptionTrendChart = buildLineChart('chart-consumption-trend', dailyLabels, [{
        label: 'Daily Consumption (kWh)',
        data: consData,
        borderColor: '#10b981',
        backgroundColor: 'rgba(16, 185, 129, 0.12)',
        tension: 0.35,
        fill: true,
        borderWidth: 2,
        pointRadius: 3
    }]);

    // 2. Solar Generation Trend Chart
    if (solarTrendChart) solarTrendChart.destroy();
    solarTrendChart = buildLineChart('chart-solar-trend', dailyLabels, [{
        label: 'Solar Generated (kWh)',
        data: solarGenData,
        borderColor: '#f59e0b',
        backgroundColor: 'rgba(245, 158, 11, 0.12)',
        tension: 0.35,
        fill: true,
        borderWidth: 2,
        pointRadius: 3
    }]);

    // 3. Hourly Diurnal Profile (Consumption vs Solar vs Solar Used)
    const hourly = charts.hourly_trends || [];
    const hourLabels = hourly.map(h => h.hour);
    const hourlyCons = hourly.map(h => h.avg_consumption);
    const hourlySolar = hourly.map(h => h.avg_solar_generated);
    const hourlySolarUsed = hourly.map(h => h.avg_solar_used);

    if (diurnalChart) diurnalChart.destroy();
    diurnalChart = buildLineChart('chart-diurnal-curve', hourLabels, [
        {
            label: 'Avg Consumption (kWh)',
            data: hourlyCons,
            borderColor: '#38bdf8',
            backgroundColor: 'rgba(56, 189, 248, 0.08)',
            borderWidth: 2.5,
            tension: 0.3,
            fill: false
        },
        {
            label: 'Avg Solar Generated (kWh)',
            data: hourlySolar,
            borderColor: '#f59e0b',
            backgroundColor: 'rgba(245, 158, 11, 0.2)',
            borderWidth: 2,
            tension: 0.35,
            fill: true
        },
        {
            label: 'Avg Solar Used (kWh)',
            data: hourlySolarUsed,
            borderColor: '#10b981',
            backgroundColor: 'rgba(16, 185, 129, 0.25)',
            borderWidth: 2,
            tension: 0.35,
            fill: true
        }
    ]);

    // 4. Building-wise Energy Consumption (Bar Chart)
    const bld = charts.building_breakdown || [];
    const bldLabels = bld.map(b => b.name);
    const bldCons = bld.map(b => b.total_consumption);

    if (buildingBarChart) buildingBarChart.destroy();
    buildingBarChart = buildBarChart('chart-building-bar', bldLabels, bldCons, 'Total kWh', '#10b981');

    // 5. Energy Distribution Doughnut Chart
    if (distributionChart) distributionChart.destroy();
    distributionChart = buildDoughnutChart('chart-energy-distribution', bldLabels, bldCons);
}

function renderAlertsTable(alerts) {
    const tbody = document.getElementById('dashboard-alerts-body');
    if (!tbody) return;

    if (!alerts || alerts.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; color: var(--text-muted);">No active wastage alerts detected.</td></tr>';
        return;
    }

    tbody.innerHTML = alerts.map(a => {
        let badgeClass = 'badge-low';
        if (a.severity === 'HIGH') badgeClass = 'badge-high';
        else if (a.severity === 'MEDIUM') badgeClass = 'badge-medium';

        return `
            <tr>
                <td style="font-weight: 600;">${a.building}</td>
                <td style="color: var(--text-dim);">${a.time}</td>
                <td>${a.issue}</td>
                <td><span class="badge ${badgeClass}">${a.severity}</span></td>
            </tr>
        `;
    }).join('');
}
