/* Arizona Datacenter Heat Analysis — Aplicação principal */

// Detecta o caminho base para os dados (funciona com Live Server e python -m http.server)
const DATA = '../data';

// ─────────────────────────────────────────────────────────────────────────────
// 1. MAPA
// ─────────────────────────────────────────────────────────────────────────────

const baseLayers = {
  satellite: L.tileLayer(
    'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    { attribution: 'Esri World Imagery', maxZoom: 19 }
  ),
  terrain: L.tileLayer(
    'https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png',
    { attribution: 'OpenTopoMap', maxZoom: 17 }
  ),
  dark: L.tileLayer(
    'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
    { attribution: 'CartoDB Dark', maxZoom: 19 }
  ),
};

const map = L.map('map', {
  center:      [33.37, -111.807],
  zoom:        11,
  zoomControl: false,
  layers:      [baseLayers.satellite],
});

L.control.zoom({ position: 'bottomright' }).addTo(map);

// ─────────────────────────────────────────────────────────────────────────────
// 2. MAPA DE CALOR
// ─────────────────────────────────────────────────────────────────────────────

let heatLayer   = null;
let heatVisible = true;
let heatOpacity = 0.85;

async function loadHeatmap() {
  try {
    const res = await fetch(`${DATA}/heatmap_bounds.json`);
    if (!res.ok) throw new Error('não encontrado');
    const b      = await res.json();
    const bounds = [[b.south, b.west], [b.north, b.east]];

    heatLayer = L.imageOverlay(`${DATA}/heatmap.png`, bounds, {
      opacity:   heatOpacity,
      className: 'heatmap-sharp',
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
    console.warn('Heatmap não disponível:', e.message);
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// 3. POLÍGONOS DOS SITES
// ─────────────────────────────────────────────────────────────────────────────

const SITE_STYLES = {
  dc:   { weight: 2, dashArray: null,  fillOpacity: 0.12 },
  mall: { weight: 2, dashArray: '5,5', fillOpacity: 0.08 },
  bbox: { weight: 1, dashArray: '6,3', fillOpacity: 0.04 },
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
        ...SITE_STYLES[f.properties.trat],
      }),
      onEachFeature: (f, layer) => {
        if (f.properties.trat === 'bbox') return;
        layer.bindTooltip(f.properties.name, {
          className: 'site-tooltip',
          sticky:    true,
          direction: 'top',
          offset:    [0, -4],
        });
        layer.on('click', () => highlightSite(f.properties.id));
      },
    }).addTo(map);
  } catch (e) {
    console.warn('Sites não carregados:', e.message);
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// 4. RESULTADOS ESTATÍSTICOS
// ─────────────────────────────────────────────────────────────────────────────

async function loadResults() {
  try {
    const res = await fetch(`${DATA}/results.json`);
    if (!res.ok) throw new Error('results.json não encontrado');
    const data = await res.json();
    renderResults(data);
    renderChart(data.series_temporais);
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
    <div style="margin-top:8px;font-size:10px;color:#777;">
      Coef. operação:
      <span style="color:#f46d43;font-weight:700;">
        ${data.coeficientes?.operacao != null
          ? (data.coeficientes.operacao>=0?'+':'')+data.coeficientes.operacao.toFixed(3)+' °K'
          : '—'}
      </span>
      &nbsp;|&nbsp; p:
      <span style="color:#f46d43;">${data.coeficientes?.operacao_pval?.toExponential(1) ?? '—'}</span>
    </div>
  `;

  const container = document.getElementById('results-container');
  container.innerHTML = '';
  (data.decomposicao || []).forEach(d => {
    const site  = (data.sites||{})[d.site] || {};
    const color = site.color || '#ff3d3d';
    const name  = site.name  || d.site;
    const sign  = d.total_anomalia >= 0 ? '+' : '';
    container.innerHTML += `
      <div class="result-card" id="card-${d.site}">
        <h3><span class="site-dot" style="background:${color}"></span>${name}</h3>
        <div class="anomaly-total">${sign}${d.total_anomalia.toFixed(2)} <span class="anomaly-unit">°K</span></div>
        <div style="font-size:10px;color:#777;margin-bottom:8px;">anomalia total PRÉ → OPS</div>
        <div class="breakdown">
          ${row('Cobertura do solo',    d.c_terreno,  d.pct_terreno,  '#fdae61')}
          ${row('Tendência regional',   d.c_geral,    d.pct_geral,    '#74add1')}
          ${row('Operação servidores',  d.c_operacao, d.pct_operacao, '#d73027')}
        </div>
      </div>`;
  });
}

function row(label, val, pct, color) {
  const sign = val >= 0 ? '+' : '';
  return `
    <div class="breakdown-row">
      <span style="width:100px;font-size:10px;color:#aaa;">${label}</span>
      <div class="breakdown-bar-wrap">
        <div class="breakdown-bar" style="width:${Math.min(Math.abs(pct),100)}%;background:${color};"></div>
      </div>
      <span class="breakdown-pct">${sign}${val.toFixed(2)}°</span>
      <span style="font-size:10px;color:#666;min-width:32px;">${Math.abs(pct).toFixed(0)}%</span>
    </div>`;
}

function renderDemoResults() {
  document.getElementById('stats-general').innerHTML = `
    <div style="font-size:11px;color:#777;text-align:center;padding:10px 0;">
      Execute <code style="color:#f46d43;">python/run_all.py</code><br>após baixar os dados do GEE
    </div>`;

  const years = Array.from({length:26},(_,i)=>2000+i);
  renderChart({
    meta:         {years, ihi: years.map(y => y>=2019 ? 1.2+(y-2019)*0.2  : (Math.random()-.5)*.4)},
    google:       {years, ihi: years.map(y => y>=2019 ? 0.9+(y-2019)*0.15 : (Math.random()-.5)*.3)},
    cyrusone:     {years, ihi: years.map(y => y>=2019 ? 0.7+(y-2019)*0.1  : (Math.random()-.5)*.3)},
    superstition: {years, ihi: years.map(() => (Math.random()-.5)*.2)},
    santan:       {years, ihi: years.map(() => (Math.random()-.5)*.2)},
  });

  const container = document.getElementById('results-container');
  container.innerHTML = '';
  [{id:'meta',name:'Meta Mesa',color:'#e53935',total:3.4,op:18},
   {id:'google',name:'Google Mesa',color:'#fb8c00',total:2.8,op:15},
   {id:'cyrusone',name:'CyrusOne Phoenix',color:'#8e24aa',total:2.1,op:20}]
  .forEach(d => {
    container.innerHTML += `
      <div class="result-card" id="card-${d.id}">
        <h3><span class="site-dot" style="background:${d.color}"></span>${d.name}
          <span style="font-size:9px;color:#555;margin-left:auto;">(demo)</span></h3>
        <div class="anomaly-total">+${d.total.toFixed(2)} <span class="anomaly-unit">°K</span></div>
        <div style="font-size:10px;color:#777;margin-bottom:8px;">estimativa preliminar</div>
        <div class="breakdown">
          ${row('Cobertura do solo',   d.total*.65, 100-d.op-10, '#fdae61')}
          ${row('Tendência regional',  d.total*.10, 10,           '#74add1')}
          ${row('Operação servidores', d.total*(d.op/100), d.op,  '#d73027')}
        </div>
      </div>`;
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// 5. CONTROLES
// ─────────────────────────────────────────────────────────────────────────────

function highlightSite(id) {
  document.querySelectorAll('.result-card').forEach(c => {
    c.style.borderColor = c.id===`card-${id}` ? 'rgba(255,61,61,.6)' : 'rgba(255,255,255,.12)';
  });
  document.getElementById(`card-${id}`)?.scrollIntoView({behavior:'smooth',block:'nearest'});
}

function setupControls() {
  document.getElementById('toggle-heat').addEventListener('change', e => {
    heatVisible = e.target.checked;
    heatLayer && (heatVisible ? heatLayer.addTo(map) : map.removeLayer(heatLayer));
  });

  const opSlider = document.getElementById('opacity-slider');
  const opVal    = document.getElementById('opacity-val');
  opSlider.addEventListener('input', e => {
    heatOpacity = e.target.value / 100;
    opVal.textContent = e.target.value + '%';
    heatLayer?.setOpacity(heatOpacity);
  });

  document.querySelectorAll('.base-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      Object.values(baseLayers).forEach(l => map.removeLayer(l));
      baseLayers[btn.dataset.layer].addTo(map);
      if (heatLayer && heatVisible) heatLayer.bringToFront();
      document.querySelectorAll('.base-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
    });
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// 6. INIT — loading sempre some, mesmo com erro
// ─────────────────────────────────────────────────────────────────────────────

function hideLoading() {
  const el = document.getElementById('loading');
  if (!el) return;
  el.classList.add('hidden');
  setTimeout(() => el.remove(), 500);
}

async function init() {
  try {
    await Promise.all([loadSites(), loadHeatmap(), loadResults()]);
    setupControls();
  } catch (e) {
    console.error('Erro na inicialização:', e);
  } finally {
    hideLoading();
  }
}

init();
