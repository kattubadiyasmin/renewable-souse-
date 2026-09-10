/**
 * WattWise - Chart.js Utility & Styling Engine
 */

// Set global Chart.js defaults for Light Theme
if (window.Chart) {
    Chart.defaults.color = '#475569';
    Chart.defaults.font.family = "'Inter', -apple-system, sans-serif";
    Chart.defaults.font.size = 12;
    Chart.defaults.plugins.tooltip.backgroundColor = '#0f172a';
    Chart.defaults.plugins.tooltip.titleColor = '#ffffff';
    Chart.defaults.plugins.tooltip.bodyColor = '#f1f5f9';
    Chart.defaults.plugins.tooltip.borderColor = '#cbd5e1';
    Chart.defaults.plugins.tooltip.borderWidth = 1;
    Chart.defaults.plugins.tooltip.padding = 10;
    Chart.defaults.plugins.tooltip.cornerRadius = 6;
}

const ChartThemes = {
    emerald: {
        border: '#059669',
        bg: 'rgba(5, 150, 105, 0.15)',
        glow: 'rgba(5, 150, 105, 0.3)'
    },
    solar: {
        border: '#d97706',
        bg: 'rgba(217, 119, 6, 0.15)',
        glow: 'rgba(217, 119, 6, 0.3)'
    },
    cyan: {
        border: '#0284c7',
        bg: 'rgba(2, 132, 199, 0.15)',
        glow: 'rgba(2, 132, 199, 0.3)'
    },
    purple: {
        border: '#7c3aed',
        bg: 'rgba(124, 58, 237, 0.15)'
    },
    rose: {
        border: '#e11d48',
        bg: 'rgba(225, 29, 72, 0.15)'
    },
    palette: [
        '#059669', '#d97706', '#0284c7', '#7c3aed', '#e11d48',
        '#2563eb', '#db2777', '#0d9488', '#4f46e5', '#ca8a04'
    ]
};

function getGridOptions() {
    return {
        color: 'rgba(226, 232, 240, 0.8)',
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
                borderColor: '#ffffff',
                borderWidth: 2,
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
