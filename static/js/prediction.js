/**
 * WattWise - Machine Learning Energy Demand Prediction Logic
 */

let predictionChart = null;

document.addEventListener('DOMContentLoaded', () => {
    runPrediction();
});

async function runPrediction() {
    const bldSelect = document.getElementById('pred-building');
    const dateInput = document.getElementById('pred-date');
    const runBtn = document.getElementById('pred-run-btn');

    const building = bldSelect.value;
    const targetDate = dateInput.value;

    const params = new URLSearchParams();
    if (building && building !== 'All') params.append('building', building);
    if (targetDate) params.append('date', targetDate);

    try {
        if (runBtn) {
            runBtn.disabled = true;
            runBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Training & Predicting...';
        }

        const res = await fetch(`/api/prediction?${params.toString()}`);
        const json = await res.json();

        if (json.status !== 'success') {
            showToast(json.message || 'Error generating forecast.', 'error');
            return;
        }

        const data = json.data;
        updatePredictionUI(data);

    } catch (err) {
        console.error(err);
        showToast('Failed to run demand prediction.', 'error');
    } finally {
        if (runBtn) {
            runBtn.disabled = false;
            runBtn.innerHTML = '<i class="fas fa-wand-magic-sparkles"></i> <span>Generate ML Forecast</span>';
        }
    }
}

function updatePredictionUI(d) {
    // 1. KPIs
    document.getElementById('pred-total-kwh').innerHTML = `${Number(d.total_predicted_demand_kwh).toLocaleString()} <span class="kpi-unit">kWh</span>`;
    
    const diffText = d.benchmark_diff_pct >= 0 
        ? `+${d.benchmark_diff_pct}% vs historical dow`
        : `${d.benchmark_diff_pct}% vs historical dow`;
    document.getElementById('pred-diff-subtext').innerHTML = `<i class="fas fa-chart-line"></i> ${diffText}`;

    document.getElementById('pred-peak-time').textContent = d.peak_time;
    document.getElementById('pred-peak-kwh-subtext').textContent = `Peak load: ${d.peak_demand_kwh} kWh`;

    document.getElementById('pred-benchmark').innerHTML = `${Number(d.historical_benchmark_kwh).toLocaleString()} <span class="kpi-unit">kWh</span>`;
    
    document.getElementById('pred-r2-score').innerHTML = `${d.model_r2_score}`;
    document.getElementById('pred-mae-subtext').textContent = `Mean Absolute Error: ${d.model_mae} kWh`;

    // 2. Banner
    const banner = document.getElementById('pred-status-banner');
    if (banner) {
        if (d.is_fallback) {
            banner.style.display = 'block';
            banner.style.backgroundColor = 'rgba(245, 158, 11, 0.15)';
            banner.style.border = '1px solid rgba(245, 158, 11, 0.35)';
            banner.style.color = '#fcd34d';
            banner.innerHTML = `<i class="fas fa-triangle-exclamation"></i> <strong>Fallback Model Active:</strong> ${d.notes}`;
        } else {
            banner.style.display = 'block';
            banner.style.backgroundColor = 'rgba(16, 185, 129, 0.15)';
            banner.style.border = '1px solid rgba(16, 185, 129, 0.35)';
            banner.style.color = '#6ee7b7';
            banner.innerHTML = `<i class="fas fa-circle-check"></i> <strong>Model Status:</strong> ${d.notes} (Trained dynamically on SQLite data)`;
        }
    }

    // 3. Model Badge
    const badge = document.getElementById('pred-model-badge');
    if (badge) badge.textContent = d.model_type;

    // 4. Forecast Chart
    const curve = d.hourly_curve || [];
    const hours = curve.map(c => c.hour);
    const demands = curve.map(c => c.predicted_demand);
    const temps = curve.map(c => c.temperature);

    if (predictionChart) predictionChart.destroy();
    predictionChart = buildLineChart('chart-prediction-curve', hours, [
        {
            label: `Forecasted Demand for ${d.selected_building} (kWh)`,
            data: demands,
            borderColor: '#8b5cf6',
            backgroundColor: 'rgba(139, 92, 246, 0.18)',
            borderWidth: 2.5,
            tension: 0.35,
            fill: true,
            pointRadius: 4,
            pointHoverRadius: 6
        },
        {
            label: 'Estimated Temperature (°C)',
            data: temps,
            borderColor: '#f59e0b',
            borderDash: [5, 5],
            borderWidth: 1.5,
            pointRadius: 2,
            yAxisID: 'y',
            fill: false
        }
    ]);
}
