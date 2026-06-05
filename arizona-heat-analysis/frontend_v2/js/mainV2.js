/* Arizona Datacenter Heat Analysis — V2 (2020-2026)
   Diferenças do V1:
   - Fundo: imagem RGB GEE (Landsat 9, 2024-2025) em vez do tile Esri
   - Heatmap: delta_lst_v2 (pre 2020-2022 vs ops 2024-2026)
   - Resultados: results_v2.json
   - Sites: CyrusOne Phoenix (DC) + Área Verde (controle)
*/

const DATA    = '../data';
const DATA_V2 = '../data';

// ─────────────────────────────────────────────────────────────────────────────
// 1. MAPA — sem tile base (será substituído pelo RGB do GEE)
// ─────────────────────────────────────────────────────────────────────────────

const map = L.map('map', {
  center:      [33.270, -111.889],
  zoom:        14,
  zoomControl: false,
  layers:      [],
});

L.control.zoom({ position: 'bottomright' }).addTo(map);

// Recalcula o tamanho do mapa quando a tela muda (rotação / resize em mobile),
// senão o Leaflet renderiza tiles cinza ou desalinhados.
let _resizeTimer = null;
function refreshMapSize() {
  clearTimeout(_resizeTimer);
  _resizeTimer = setTimeout(() => map.invalidateSize(), 200);
}
window.addEventListener('resize', refreshMapSize);
window.addEventListener('orientationchange', refreshMapSize);

// ─────────────────────────────────────────────────────────────────────────────
// 2. IMAGEM RGB DE FUNDO (GEE Landsat 9, 2024-2025)
// ─────────────────────────────────────────────────────────────────────────────

let rgbLayer   = null;
let rgbVisible = true;

async function loadRGBBackground() {
  try {
    const res = await fetch(`${DATA_V2}/rgb_bounds.json`);
    if (!res.ok) throw new Error('rgb_bounds.json não encontrado');
    const b      = await res.json();
    const bounds = [[b.south, b.west], [b.north, b.east]];

    rgbLayer = L.imageOverlay(`${DATA_V2}/rgb_background.png`, bounds, {
      opacity:     1.0,
      interactive: false,
      className:   'rgb-background',
    });

    rgbLayer.addTo(map);
  } catch (e) {
    console.warn('[V2] RGB background não disponível:', e.message);
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// 3. MAPA DE CALOR V2
// ─────────────────────────────────────────────────────────────────────────────

let heatLayer   = null;
let heatVisible = true;
let heatOpacity = 0.85;

async function loadHeatmap() {
  try {
    const res = await fetch(`${DATA_V2}/heatmap_bounds_v2.json`);
    if (!res.ok) throw new Error('heatmap_bounds_v2.json não encontrado');
    const b      = await res.json();
    const bounds = [[b.south, b.west], [b.north, b.east]];

    heatLayer = L.imageOverlay(`${DATA_V2}/heatmap_v2.png`, bounds, {
      opacity:     heatOpacity,
      className:   'heatmap-sharp',
      interactive: false,
    });

    if (heatVisible) heatLayer.addTo(map);

    const style = document.createElement('style');
    style.textContent = `
      .heatmap-sharp img {
        image-rendering: pixelated;
        image-rendering: crisp-edges;
        filter: contrast(1.2) saturate(1.4);
      }
    `;
    document.head.appendChild(style);
  } catch (e) {
    console.warn('[V2] Heatmap v2 não disponível:', e.message);
    console.info('[V2] Execute python generate_heatmap_v2.py para gerar heatmap_v2.png');
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// 4. POLÍGONOS DOS SITES V2
// ─────────────────────────────────────────────────────────────────────────────

const SITE_STYLES = {
  dc:    { weight: 2, dashArray: null,  fillOpacity: 0.15 },
  green: { weight: 2, dashArray: '5,5', fillOpacity: 0.12 },
  bbox:  { weight: 1, dashArray: '6,3', fillOpacity: 0.04 },
};

async function loadSites() {
  try {
    const res  = await fetch(`${DATA}/sites.geojson`);
    if (!res.ok) throw new Error('sites.geojson não encontrado');
    const data = await res.json();

    L.geoJSON(data, {
      style: f => ({
        color:     f.properties.color,
        fillColor: f.properties.color,
        ...(SITE_STYLES[f.properties.trat] || SITE_STYLES.bbox),
      }),
      onEachFeature: (f, layer) => {
        if (f.properties.trat === 'bbox') return;

        const tip = document.getElementById('map-tip');
        if (f.properties.id === 'cyrusone') {
          layer.on('mouseover', ()  => { tip.style.display = 'block'; });
          layer.on('mousemove', e   => {
            tip.style.left = (e.originalEvent.clientX + 14) + 'px';
            tip.style.top  = (e.originalEvent.clientY - 36) + 'px';
          });
          layer.on('mouseout', ()   => { tip.style.display = 'none'; });
        } else {
          layer.bindTooltip(f.properties.name, {
            className: 'site-tooltip', sticky: true, direction: 'top', offset: [0, -4],
          });
        }

        layer.on('click', () => highlightSite(f.properties.id));
      },
    }).addTo(map);
  } catch (e) {
    console.warn('[V2] Sites não carregados:', e.message);
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// 5. RESULTADOS V2
// ─────────────────────────────────────────────────────────────────────────────

async function loadResults() {
  try {
    const res = await fetch(`${DATA_V2}/results_v2.json`);
    if (!res.ok) throw new Error('results_v2.json não encontrado');
    const data = await res.json();
    renderResults(data);
  } catch {
    renderDemoResults();
  }
}

function renderResults(data) {
  document.getElementById('stats-general').innerHTML = `
    <div class="stat-grid">
      <div class="stat-item">
        <div class="stat-value">${data.n_obs?.toLocaleString() ?? '—'}</div>
        <div class="stat-label">Observações</div>
      </div>
      <div class="stat-item">
        <div class="stat-value">${data.r2 ? (data.r2*100).toFixed(1)+'%' : '—'}</div>
        <div class="stat-label">R² do modelo</div>
      </div>
    </div>
    <div style="margin-top:8px;font-size:10px;color:var(--text-muted);">
      Coef. operação:
      <span style="color:#ff9800;font-weight:700;">
        ${data.coeficientes?.operacao != null
          ? (data.coeficientes.operacao>=0?'+':'')+data.coeficientes.operacao.toFixed(3)+' °K'
          : '—'}
      </span>
      &nbsp;|&nbsp; p:
      <span style="color:#ff9800;">${data.coeficientes?.operacao_pval?.toExponential(1) ?? '—'}</span>
    </div>
  `;

  const container = document.getElementById('results-container');
  container.innerHTML = '';
  (data.decomposicao || []).forEach(d => {
    const site  = (data.sites||{})[d.site] || {};
    const color = site.color || '#ff9800';
    const name  = site.name  || d.site;
    const total = isNaN(d.total_anomalia) ? null : d.total_anomalia;
    const sign  = total !== null && total >= 0 ? '+' : '';
    container.innerHTML += `
      <div class="result-card" id="card-${d.site}">
        <h3><span class="site-dot" style="background:${color}"></span>${name}</h3>
        <div class="anomaly-total">
          ${total !== null ? sign+total.toFixed(2) : '—'}
          <span class="anomaly-unit">°K</span>
        </div>
        <div style="font-size:10px;color:var(--text-muted);margin-bottom:8px;">anomalia total PRÉ → OPS (v2)</div>
        <div class="breakdown">
          ${row('Cobertura do solo',    d.c_terreno,  d.pct_terreno,  '#fdae61')}
          ${row('Tendência regional',   d.c_geral,    d.pct_geral,    '#74add1')}
          ${row('Operação servidores',  d.c_operacao, d.pct_operacao, '#d73027')}
        </div>
      </div>`;
  });

  if (data.series_temporais && Object.keys(data.series_temporais).length > 0) {
    document.getElementById('chart-section').style.display = 'block';
    renderChart(data.series_temporais);
  }
}

function row(label, val, pct, color) {
  if (val == null || isNaN(val)) return `
    <div class="breakdown-row">
      <span style="width:100px;font-size:10px;color:#aaa;">${label}</span>
      <span style="font-size:10px;color:var(--text-dim);">—</span>
    </div>`;
  const sign = val >= 0 ? '+' : '';
  return `
    <div class="breakdown-row">
      <span style="width:100px;font-size:10px;color:#aaa;">${label}</span>
      <div class="breakdown-bar-wrap">
        <div class="breakdown-bar" style="width:${Math.min(Math.abs(pct||0),100)}%;background:${color};"></div>
      </div>
      <span class="breakdown-pct">${sign}${val.toFixed(2)}°</span>
      <span style="font-size:10px;color:var(--text-dim);min-width:32px;">${Math.abs(pct||0).toFixed(0)}%</span>
    </div>`;
}

function renderDemoResults() {
  document.getElementById('stats-general').innerHTML = `
    <div style="font-size:11px;color:var(--text-muted);text-align:center;padding:10px 0;">
      Execute <code style="color:#ff9800;">python/analysis_v2.py</code><br>para gerar os resultados v2
    </div>`;
}

// ─────────────────────────────────────────────────────────────────────────────
// 6. CONTROLES
// ─────────────────────────────────────────────────────────────────────────────

function highlightSite(id) {
  document.querySelectorAll('.result-card').forEach(c => {
    c.style.borderColor = c.id===`card-${id}` ? 'rgba(255,152,0,.6)' : 'rgba(255,255,255,.12)';
  });
  document.getElementById(`card-${id}`)?.scrollIntoView({behavior:'smooth', block:'nearest'});
}

function setupControls() {
  document.getElementById('toggle-heat').addEventListener('change', e => {
    heatVisible = e.target.checked;
    heatLayer && (heatVisible ? heatLayer.addTo(map) : map.removeLayer(heatLayer));
  });

  document.getElementById('toggle-rgb').addEventListener('change', e => {
    rgbVisible = e.target.checked;
    rgbLayer && (rgbVisible ? rgbLayer.addTo(map) : map.removeLayer(rgbLayer));
  });

  const opSlider = document.getElementById('opacity-slider');
  const opVal    = document.getElementById('opacity-val');
  opSlider.addEventListener('input', e => {
    heatOpacity = e.target.value / 100;
    opVal.textContent = e.target.value + '%';
    heatLayer?.setOpacity(heatOpacity);
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// 7. INIT
// ─────────────────────────────────────────────────────────────────────────────

function hideLoading() {
  const el = document.getElementById('loading');
  if (!el) return;
  el.classList.add('hidden');
  setTimeout(() => el.remove(), 500);
}

async function init() {
  try {
    await loadRGBBackground();
    await Promise.all([loadSites(), loadHeatmap(), loadResults()]);
    setupControls();
  } catch (e) {
    console.error('[V2] Erro na inicialização:', e);
  } finally {
    hideLoading();
  }
}

init();
