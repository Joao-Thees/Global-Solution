/* Arizona Heat Analysis V2 — Gráficos de série temporal (2020-2026) */

const SITE_COLORS = {
  cyrusone:   '#FF6600',
  area_verde: '#00AA00',
};

const SITE_LABELS = {
  cyrusone:   'CyrusOne Phoenix (DC)',
  area_verde: 'Área Verde (controle)',
};

let chartInstance = null;

function renderChart(seriesData) {
  const ctx = document.getElementById('time-chart');
  if (!ctx) return;

  const datasets = Object.entries(seriesData)
    .filter(([id]) => SITE_COLORS[id])
    .map(([id, s]) => ({
      label:           SITE_LABELS[id] || id,
      data:            s.years.map((y, i) => ({ x: y, y: s.ihi[i] })),
      borderColor:     SITE_COLORS[id],
      backgroundColor: SITE_COLORS[id] + '22',
      pointRadius:     3,
      pointHoverRadius:6,
      borderWidth:     2,
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
          labels: { color: '#ccc', boxWidth: 12, font: { size: 10 } },
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
              xMin:        2024,
              xMax:        2024,
              borderColor: 'rgba(255,152,0,0.6)',
              borderWidth: 1,
              borderDash:  [4, 4],
              label: {
                display:  true,
                content:  'Ops v2 →',
                color:    '#ff9800',
                font:     { size: 9 },
                position: 'start',
              },
            },
            preEnd: {
              type:        'line',
              xMin:        2022,
              xMax:        2022,
              borderColor: 'rgba(141,209,116,0.4)',
              borderWidth: 1,
              borderDash:  [4, 4],
              label: {
                display:  true,
                content:  '← Pré',
                color:    '#8dd174',
                font:     { size: 9 },
                position: 'start',
              },
            },
          },
        },
      },
      scales: {
        x: {
          type:  'linear',
          ticks: { color: '#777', font: { size: 10 }, stepSize: 1 },
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
