/**
 * WattWise - Chart.js Utility & Styling Engine
 */

// Set global Chart.js defaults
if (window.Chart) {
    Chart.defaults.color = '#94a3b8';
    Chart.defaults.font.family = "'Inter', -apple-system, sans-serif";
    Chart.defaults.font.size = 12;
    Chart.defaults.plugins.tooltip.backgroundColor = '#0f172a';
    Chart.defaults.plugins.tooltip.titleColor = '#f8fafc';
    Chart.defaults.plugins.tooltip.bodyColor = '#cbd5e1';
    Chart.defaults.plugins.tooltip.borderColor = '#334155';
    Chart.defaults.plugins.tooltip.borderWidth = 1;
    Chart.defaults.plugins.tooltip.padding = 10;
    Chart.defaults.plugins.tooltip.cornerRadius = 6;
}

const ChartThemes = {
    emerald: {
        border: '#10b981',
        bg: 'rgba(16, 185, 129, 0.15)',
        glow: 'rgba(16, 185, 129, 0.4)'
    },
    solar: {
        border: '#f59e0b',
        bg: 'rgba(245, 158, 11, 0.15)',
        glow: 'rgba(245, 158, 11, 0.4)'
    },
    cyan: {
        border: '#06b6d4',
        bg: 'rgba(6, 182, 212, 0.15)',
        glow: 'rgba(6, 182, 212, 0.4)'
    },
    purple: {
        border: '#8b5cf6',
        bg: 'rgba(139, 92, 246, 0.15)'
    },
    rose: {
        border: '#f43f5e',
        bg: 'rgba(244, 63, 94, 0.15)'
    },
    palette: [
        '#10b981', '#f59e0b', '#06b6d4', '#8b5cf6', '#f43f5e',
        '#3b82f6', '#ec4899', '#14b8a6', '#6366f1', '#eab308'
    ]
};

function getGridOptions() {
    return {
        color: 'rgba(51, 65, 85, 0.35)',
        drawBorder: false
    };
}

function buildLineChart(canvasId, labels, datasets, yLabel = 'kWh') {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: { boxWidth: 12, usePointStyle: true, padding: 16 }
                }
            },
            scales: {
                x: {
                    grid: getGridOptions(),
                    ticks: { maxRotation: 45 }
                },
                y: {
                    grid: getGridOptions(),
                    title: { display: true, text: yLabel, color: '#64748b' }
                }
            }
        }
    });
}

function buildBarChart(canvasId, labels, data, label = 'Energy (kWh)', color = '#10b981') {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: label,
                data: data,
                backgroundColor: color,
                borderRadius: 6,
                borderSkipped: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: { grid: { display: false } },
                y: {
                    grid: getGridOptions(),
                    title: { display: true, text: label, color: '#64748b' }
                }
            }
        }
    });
}

function buildDoughnutChart(canvasId, labels, data, colors = ChartThemes.palette) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return null;

    return new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors.slice(0, data.length),
                borderColor: '#1e293b',
                borderWidth: 3,
                hoverOffset: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '68%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { boxWidth: 10, usePointStyle: true, padding: 14 }
                }
            }
        }
    });
}
