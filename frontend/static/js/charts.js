// charts.js — Chart.js (Minimalist Black & White Monochrome Theme)

const chartDefaults = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: {
            labels: {
                color: '#D4D4D8',
                font: { family: 'Plus Jakarta Sans', size: 12 },
                padding: 16
            }
        },
        tooltip: {
            backgroundColor: 'rgba(18, 18, 20, 0.95)',
            titleColor: '#FFFFFF',
            bodyColor: '#FFFFFF',
            borderColor: 'rgba(255, 255, 255, 0.3)',
            borderWidth: 1,
            cornerRadius: 8,
            padding: 12
        }
    },
    scales: {
        x: {
            ticks: { color: '#71717A', font: { family: 'Plus Jakarta Sans', size: 11 } },
            grid: { color: 'rgba(255, 255, 255, 0.06)' }
        },
        y: {
            ticks: { color: '#71717A', font: { family: 'Plus Jakarta Sans', size: 11 } },
            grid: { color: 'rgba(255, 255, 255, 0.06)' },
            beginAtZero: true
        }
    }
};

function initWeeklyChart(elementId, data) {
    const ctx = document.getElementById(elementId);
    if (!ctx || !data) return;

    const labels = data.map(d => d.date);
    const values = data.map(d => d.count);

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Present Students',
                data: values,
                borderColor: '#FFFFFF',
                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                borderWidth: 2.5,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#FFFFFF',
                pointBorderColor: '#000000',
                pointBorderWidth: 2,
                pointRadius: 5
            }]
        },
        options: {
            ...chartDefaults,
            plugins: {
                ...chartDefaults.plugins,
                legend: { display: false }
            }
        }
    });
}

function initDepartmentChart(elementId, data) {
    const ctx = document.getElementById(elementId);
    if (!ctx || !data || data.length === 0) return;

    const labels = data.map(d => d.department);
    const values = data.map(d => d.count);

    const monoColors = [
        '#FFFFFF',
        '#E4E4E7',
        '#D4D4D8',
        '#A1A1AA',
        '#71717A',
        '#FFFFFF',
        '#E4E4E7'
    ];

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Present Today',
                data: values,
                backgroundColor: monoColors.slice(0, labels.length),
                borderRadius: 6,
                borderSkipped: false
            }]
        },
        options: {
            ...chartDefaults,
            plugins: {
                ...chartDefaults.plugins,
                legend: { display: false }
            }
        }
    });
}

function initMaskChart(elementId, maskCount, noMaskCount) {
    const ctx = document.getElementById(elementId);
    if (!ctx) return;

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['With Mask', 'Without Mask'],
            datasets: [{
                data: [maskCount || 0, noMaskCount || 0],
                backgroundColor: ['#FFFFFF', '#71717A'],
                borderColor: '#18181B',
                borderWidth: 3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '70%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#D4D4D8', font: { family: 'Plus Jakarta Sans' } }
                }
            }
        }
    });
}
