/* Arizona Heat Analysis — Gráficos de série temporal */

const SITE_COLORS = {
  meta:         '#e53935',
  google:       '#fb8c00',
  cyrusone:     '#8e24aa',
  superstition: '#1e88e5',
  santan:       '#43a047',
};

const SITE_LABELS = {
  meta:         'Meta Mesa',
  google:       'Google Mesa',
  cyrusone:     'CyrusOne',
  superstition: 'Superstition (controle)',
  santan:       'SanTan (controle)',
};

let chartInstance = null;

function renderChart(seriesData) {
  const ctx = document.getElementById('time-chart');
  if (!ctx) return;

  const datasets = Object.entries(seriesData).map(([id, s]) => ({
    label:           SITE_LABELS[id] || id,
    data:            s.years.map((y, i) => ({ x: y, y: s.ihi[i] })),
    borderColor:     SITE_COLORS[id] || '#aaa',
    backgroundColor: (SITE_COLORS[id] || '#aaa') + '22',
    pointRadius:     2,
    pointHoverRadius:5,
    borderWidth:     1.5,
    tension:         0.3,
    fill:            false,
  }));

  if (chartInstance) {
    chartInstance.data.datasets = datasets;
    chartInstance.update();
    return;
  }

  chartInstance = new Chart(ctx, {
    type: 'line',
    data: { datasets },
    options: {
      responsive:          true,
      maintainAspectRatio: false,
      animation:           { duration: 600 },
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: {
          display: true,
          labels: {
            color:    '#ccc',
            boxWidth: 12,
            font:     { size: 10 },
          },
        },
        tooltip: {
          backgroundColor: 'rgba(13,13,13,0.9)',
          titleColor:      '#fff',
          bodyColor:       '#ccc',
          callbacks: {
            label: ctx => ` ${ctx.dataset.label}: ${ctx.parsed.y.toFixed(2)} °K`,
          },
        },
        annotation: {
          annotations: {
            opsStart: {
              type:        'line',
              xMin:        2019,
              xMax:        2019,
              borderColor: 'rgba(255,61,61,0.5)',
              borderWidth: 1,
              borderDash:  [4, 4],
              label: {
                display:     true,
                content:     'Ops →',
                color:       '#ff3d3d',
                font:        { size: 9 },
                position:    'start',
              },
            },
          },
        },
      },
      scales: {
        x: {
          type:  'linear',
          title: { display: false },
          ticks: { color: '#777', font: { size: 10 }, stepSize: 5 },
          grid:  { color: 'rgba(255,255,255,0.06)' },
        },
        y: {
          title: {
            display: true,
            text:    'IHI (°K)',
            color:   '#777',
            font:    { size: 10 },
          },
          ticks: { color: '#777', font: { size: 10 } },
          grid:  { color: 'rgba(255,255,255,0.06)' },
        },
      },
    },
  });
}
