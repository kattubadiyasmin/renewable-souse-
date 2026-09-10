/**
 * WattWise - Analytics Dashboard Logic
 */

let analyticsDailyChart = null;
let analyticsBuildingChart = null;

document.addEventListener('DOMContentLoaded', () => {
    loadAnalytics();
});

function resetFilters() {
    document.getElementById('filter-building').value = 'All';
    document.getElementById('filter-date-from').value = '';
    document.getElementById('filter-date-to').value = '';
    loadAnalytics();
}

async function loadAnalytics() {
    const building = document.getElementById('filter-building').value;
    const dateFrom = document.getElementById('filter-date-from').value;
    const dateTo = document.getElementById('filter-date-to').value;

    const params = new URLSearchParams();
    if (building && building !== 'All') params.append('building', building);
    if (dateFrom) params.append('date_from', dateFrom);
    if (dateTo) params.append('date_to', dateTo);

    try {
        const res = await fetch(`/api/analytics?${params.toString()}`);
        const json = await res.json();

        if (json.status !== 'success') {
            showToast(json.message || 'Error fetching analytics.', 'error');
            return;
        }

        const data = json.data;
        updateAnalyticsStats(data);
        updateAnalyticsInsights(data.dynamic_insights);
        renderAnalyticsCharts(data);
        renderBuildingTable(data.building_breakdown);

    } catch (err) {
        console.error(err);
        showToast('Failed to load energy analytics.', 'error');
    }
}

function updateAnalyticsStats(d) {
    document.getElementById('stat-total-cons').innerHTML = `${Number(d.total_consumption).toLocaleString()} <span class="kpi-unit">kWh</span>`;
    document.getElementById('stat-avg-cons').innerHTML = `${Number(d.average_consumption).toFixed(2)} <span class="kpi-unit">kWh</span>`;
    document.getElementById('stat-max-cons').innerHTML = `${Number(d.max_consumption).toFixed(1)} <span class="kpi-unit">kWh</span>`;
    
    if (d.max_record) {
        document.getElementById('stat-max-subtext').textContent = `${d.max_record.building} on ${d.max_record.date} ${d.max_record.time}`;
    }

    document.getElementById('stat-min-cons').innerHTML = `${Number(d.min_consumption).toFixed(1)} <span class="kpi-unit">kWh</span>`;
    if (d.min_record) {
        document.getElementById('stat-min-subtext').textContent = `${d.min_record.building} at ${d.min_record.time}`;
    }

    document.getElementById('stat-peak-window').textContent = d.peak_usage_time;
    document.getElementById('stat-solar-util').innerHTML = `${d.solar_utilization_pct} <span class="kpi-unit">%</span>`;
    document.getElementById('stat-solar-subtext').textContent = `${Number(d.total_solar_used).toLocaleString()} of ${Number(d.total_solar_generated).toLocaleString()} kWh`;
}

function updateAnalyticsInsights(insights) {
    const list = document.getElementById('analytics-insights-list');
    if (!list) return;

    if (!insights || !insights.length) {
        list.innerHTML = '<li class="insight-item">No specific pattern alerts detected for current filter.</li>';
        return;
    }

    list.innerHTML = insights.map(txt => `
        <li class="insight-item">
            <i class="fas fa-chart-line"></i>
            <span>${txt}</span>
        </li>
    `).join('');
}

function renderAnalyticsCharts(d) {
    // 1. Daily Trend
    const daily = d.daily_trends || [];
    const dates = daily.map(item => item.date.substring(5));
    const cons = daily.map(item => item.consumption);
    const solar = daily.map(item => item.solar_generated);

    if (analyticsDailyChart) analyticsDailyChart.destroy();
    analyticsDailyChart = buildLineChart('chart-analytics-daily', dates, [
        {
            label: 'Consumption (kWh)',
            data: cons,
            borderColor: '#10b981',
            backgroundColor: 'rgba(16, 185, 129, 0.12)',
            borderWidth: 2,
            tension: 0.3,
            fill: true
        },
        {
            label: 'Solar Generated (kWh)',
            data: solar,
            borderColor: '#f59e0b',
            backgroundColor: 'rgba(245, 158, 11, 0.12)',
            borderWidth: 2,
            tension: 0.3,
            fill: true
        }
    ]);

    // 2. Building bar
    const bld = d.building_breakdown || [];
    const bldNames = bld.map(b => b.name);
    const bldCons = bld.map(b => b.total_consumption);

    if (analyticsBuildingChart) analyticsBuildingChart.destroy();
    analyticsBuildingChart = buildBarChart('chart-analytics-building', bldNames, bldCons, 'Total Load (kWh)', '#06b6d4');
}

function renderBuildingTable(buildings) {
    const tbody = document.getElementById('analytics-building-body');
    if (!tbody) return;

    if (!buildings || !buildings.length) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; color: var(--text-dim);">No building data matching filters.</td></tr>';
        return;
    }

    tbody.innerHTML = buildings.map(b => `
        <tr>
            <td style="font-weight: 600;">${b.name}</td>
            <td><span class="card-badge">${b.type}</span></td>
            <td style="color: var(--primary); font-weight: 600;">${Number(b.total_consumption).toLocaleString()}</td>
            <td>${b.avg_consumption}</td>
            <td>${b.max_consumption}</td>
            <td style="color: var(--solar);">${Number(b.solar_generated).toLocaleString()}</td>
            <td>${Number(b.solar_used).toLocaleString()}</td>
            <td><strong style="color: var(--cyan);">${b.share_pct}%</strong></td>
        </tr>
    `).join('');
}
