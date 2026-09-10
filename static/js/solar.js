/**
 * WattWise - Solar Analysis Charts & Telemetry Logic
 */

let solarHourlyChart = null;
let solarDonutChart = null;
let solarDailyChart = null;
let weatherChart = null;

document.addEventListener('DOMContentLoaded', () => {
    loadSolarData();
});

async function loadSolarData() {
    try {
        const res = await fetch('/api/solar');
        const json = await res.json();

        if (json.status !== 'success') {
            showToast(json.message || 'Error fetching solar telemetry.', 'error');
            return;
        }

        const data = json.data;
        updateSolarKPIs(data);
        updateSolarInsights(data.insights);
        renderSolarCharts(data);

    } catch (err) {
        console.error(err);
        showToast('Failed to load solar data.', 'error');
    }
}

function updateSolarKPIs(d) {
    document.getElementById('sol-total-gen').innerHTML = `${Number(d.total_solar_generated).toLocaleString()} <span class="kpi-unit">kWh</span>`;
    document.getElementById('sol-total-used').innerHTML = `${Number(d.total_solar_used).toLocaleString()} <span class="kpi-unit">kWh</span>`;
    document.getElementById('sol-unused').innerHTML = `${Number(d.unused_solar).toLocaleString()} <span class="kpi-unit">kWh</span>`;
    document.getElementById('sol-util-pct').innerHTML = `${d.solar_utilization_pct} <span class="kpi-unit">%</span>`;
    document.getElementById('sol-renew-fraction').innerHTML = `${d.renewable_fraction_pct} <span class="kpi-unit">%</span>`;
    document.getElementById('sol-peak-window').textContent = d.peak_solar_window;
    
    const peakSub = document.getElementById('sol-peak-yield-subtext');
    if (peakSub) {
        peakSub.textContent = `Avg peak output: ${d.peak_hourly_yield_kwh} kWh`;
    }
}

function updateSolarInsights(insights) {
    const list = document.getElementById('solar-insights-list');
    if (!list) return;

    if (!insights || !insights.length) {
        list.innerHTML = '<li class="insight-item">Sufficient solar generation detected across daytime hours.</li>';
        return;
    }

    list.innerHTML = insights.map(txt => `
        <li class="insight-item">
            <i class="fas fa-sun" style="color: var(--solar);"></i>
            <span>${txt}</span>
        </li>
    `).join('');
}

function renderSolarCharts(d) {
    // 1. Hourly Solar Generation vs Usage Curve
    const hourly = d.hourly_solar_profile || [];
    const hours = hourly.map(h => h.hour);
    const genData = hourly.map(h => h.solar_generated);
    const usedData = hourly.map(h => h.solar_used);

    if (solarHourlyChart) solarHourlyChart.destroy();
    solarHourlyChart = buildLineChart('chart-solar-hourly', hours, [
        {
            label: 'Solar Generated (kWh)',
            data: genData,
            borderColor: '#f59e0b',
            backgroundColor: 'rgba(245, 158, 11, 0.25)',
            borderWidth: 2,
            tension: 0.35,
            fill: true
        },
        {
            label: 'Solar Directly Used (kWh)',
            data: usedData,
            borderColor: '#10b981',
            backgroundColor: 'rgba(16, 185, 129, 0.3)',
            borderWidth: 2,
            tension: 0.35,
            fill: true
        }
    ]);

    // 2. Solar Used vs Unused Doughnut Chart
    if (solarDonutChart) solarDonutChart.destroy();
    solarDonutChart = buildDoughnutChart(
        'chart-solar-donut',
        ['Directly Used (kWh)', 'Unused Curtailment (kWh)'],
        [d.total_solar_used, d.unused_solar],
        ['#10b981', '#f59e0b']
    );

    // 3. Daily Renewable Contribution Trend
    const daily = d.daily_solar_trend || [];
    const dates = daily.map(item => item.date.substring(5));
    const dailyGen = daily.map(item => item.solar_generated);
    const dailyUsed = daily.map(item => item.solar_used);

    if (solarDailyChart) solarDailyChart.destroy();
    solarDailyChart = buildLineChart('chart-solar-daily-trend', dates, [
        {
            label: 'Daily Generation (kWh)',
            data: dailyGen,
            borderColor: '#f59e0b',
            backgroundColor: 'rgba(245, 158, 11, 0.1)',
            borderWidth: 2,
            tension: 0.3,
            fill: false
        },
        {
            label: 'Daily Used (kWh)',
            data: dailyUsed,
            borderColor: '#10b981',
            backgroundColor: 'rgba(16, 185, 129, 0.15)',
            borderWidth: 2,
            tension: 0.3,
            fill: true
        }
    ]);

    // 4. Weather Efficiency Impact Bar Chart
    const weather = d.weather_efficiency || [];
    const wLabels = weather.map(w => w.weather);
    const wYields = weather.map(w => w.avg_solar_reading);

    if (weatherChart) weatherChart.destroy();
    weatherChart = buildBarChart('chart-weather-efficiency', wLabels, wYields, 'Avg PV Reading (kWh)', '#f59e0b');
}
