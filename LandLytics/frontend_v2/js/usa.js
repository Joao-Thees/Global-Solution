// Mapa nacional dos Estados Unidos com Mapbox GL JS.
// Mostra apenas data centers reais (localizacao verificada em catalogos publicos).
// Phoenix e a porta de entrada: clicar nele abre o painel real de satelite (indexV2.html).

// Token do Mapbox: lido de js/config.js (NAO versionado, gerado por python/main.py
// a partir da variavel de ambiente MAPBOX_TOKEN). Veja o README ("Configurar o Mapbox").
const MAPBOX_TOKEN = (window.LANDLYTICS_CONFIG && window.LANDLYTICS_CONFIG.MAPBOX_TOKEN) || '';

const DATA_URL = './data/datacenters_usa.json';
const US_CENTER = [-98.35, 39.5];
const US_ZOOM = 3.4;

const els = {
  map: document.getElementById('map'),
  state: document.getElementById('stateFilter'),
  toggleMarkers: document.getElementById('toggleMarkers'),
  totalSites: document.getElementById('totalSites'),
  totalMw: document.getElementById('totalMw'),
  statesCount: document.getElementById('statesCount'),
  rankList: document.getElementById('rankList'),
  resetBtn: document.getElementById('resetBtn'),
};

let map;
let allData = [];
let filteredData = [];
let entries = []; // cada item: { d, marker, el }

start();

function start() {
  // sem token configurado: avisa de forma amigável em vez de quebrar
  if (!MAPBOX_TOKEN) {
    console.error('[USA] MAPBOX_TOKEN ausente. Defina a variável de ambiente e rode ' +
      '"python python/main.py" para gerar js/config.js (veja o README, "Configurar o Mapbox").');
    if (els.map) {
      els.map.classList.add('map-config-msg');
      els.map.innerHTML =
        'Configure o token do Mapbox para carregar o mapa.<br>' +
        'Defina a variável <code>MAPBOX_TOKEN</code> e rode <code>python python/main.py</code> ' +
        '(veja o README).';
    }
    return;
  }

  mapboxgl.accessToken = MAPBOX_TOKEN;
  map = new mapboxgl.Map({
    container: 'map',
    style: 'mapbox://styles/mapbox/dark-v11',
    center: US_CENTER,
    zoom: US_ZOOM,
    attributionControl: true,
  });
  map.addControl(new mapboxgl.NavigationControl({ showCompass: false }), 'bottom-right');

  map.on('load', init);
}

async function init() {
  try {
    const res = await fetch(DATA_URL);
    allData = await res.json();
  } catch (err) {
    console.error('Nao foi possivel carregar os data centers:', err);
    return;
  }
  filteredData = [...allData];

  addMarkers();
  populateStateFilter();
  bindEvents();
  render();
}

// um marcador HTML por data center, com Phoenix destacado como porta de entrada
function addMarkers() {
  allData.forEach(d => {
    const el = document.createElement('div');
    el.className = 'dc-marker' + (d.entry ? ' entry' : '');
    el.style.position = 'relative';
    el.setAttribute('role', 'button');
    el.setAttribute('tabindex', '0');
    el.setAttribute('aria-label',
      `${d.name}, ${d.city}, ${d.state}` + (d.entry ? '. Abrir analise de satelite.' : ''));

    if (d.entry) {
      const flag = document.createElement('span');
      flag.className = 'entry-flag';
      flag.textContent = 'Ver satelite';
      el.appendChild(flag);
    }

    const marker = new mapboxgl.Marker({ element: el }).setLngLat([d.lng, d.lat]).addTo(map);

    // clicar (ou Enter) em Phoenix vai para o painel; nos demais abre o popup
    const activate = () => handleMarkerClick(d);
    el.addEventListener('click', activate);
    el.addEventListener('keydown', e => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); activate(); }
    });

    entries.push({ d, marker, el });
  });
}

function handleMarkerClick(d) {
  if (d.entry && d.link) {
    window.location.href = d.link;
    return;
  }
  new mapboxgl.Popup({ offset: 16, closeButton: true })
    .setLngLat([d.lng, d.lat])
    .setHTML(popupHTML(d))
    .addTo(map);
  map.flyTo({ center: [d.lng, d.lat], zoom: Math.max(map.getZoom(), 6) });
}

function popupHTML(d) {
  const isReal = d.data_source === 'real';
  // a capacidade so aparece quando ha um numero para o site
  const capacity = d.capacity_mw
    ? `<p><strong>Capacidade:</strong> ${d.capacity_mw} MW</p>`
    : '';
  const dlt = (typeof d.delta_lst === 'number')
    ? `<p><strong>&Delta;LST:</strong> +${d.delta_lst.toFixed(1)} °C ${isReal ? '(real)' : '(simulado)'}</p>`
    : '';
  const note = d.note ? `<p>${d.note}</p>` : '';
  const badge = isReal
    ? '<span class="badge badge--real">Dados reais · satélite</span>'
    : '<span class="badge badge--sim">Localização real · dados simulados</span>';
  return `
    <div class="dc-popup">
      <h3>${d.name}</h3>
      <p><strong>Local:</strong> ${d.city}, ${d.state}</p>
      <p><strong>Operador:</strong> ${d.company}</p>
      <p><strong>Status:</strong> ${translateStatus(d.status)}</p>
      ${capacity}
      ${dlt}
      ${note}
      ${badge}
    </div>`;
}

function populateStateFilter() {
  const states = [...new Set(allData.map(d => d.state))].sort();
  states.forEach(st => {
    const opt = document.createElement('option');
    opt.value = st;
    opt.textContent = st;
    els.state.appendChild(opt);
  });
}

function bindEvents() {
  els.state.addEventListener('change', applyFilters);
  els.toggleMarkers.addEventListener('change', updateMarkerVisibility);

  els.resetBtn.addEventListener('click', () => {
    els.state.value = 'all';
    applyFilters();
    map.flyTo({ center: US_CENTER, zoom: US_ZOOM });
  });
}

function applyFilters() {
  const st = els.state.value;
  filteredData = allData.filter(d => st === 'all' || d.state === st);
  render();
}

function render() {
  updateMarkerVisibility();
  renderMetrics();
  renderRanking();
}

// mostra so os marcadores que passaram pelo filtro (e respeita o toggle geral)
function updateMarkerVisibility() {
  const ids = new Set(filteredData.map(d => d.id));
  entries.forEach(({ d, el }) => {
    const visible = els.toggleMarkers.checked && ids.has(d.id);
    el.style.display = visible ? 'block' : 'none';
  });
}

// metricas reais: contagem, soma da capacidade conhecida e numero de estados
function renderMetrics() {
  els.totalSites.textContent = filteredData.length;

  const totalMw = filteredData.reduce((sum, d) => sum + (d.capacity_mw || 0), 0);
  els.totalMw.textContent = totalMw;

  els.statesCount.textContent = new Set(filteredData.map(d => d.state)).size;
}

// lista os data centers analisados, maiores capacidades conhecidas primeiro.
// Cada item mostra operador, MW e ΔLST, com selo REAL (Phoenix) vs SIMULADO.
function renderRanking() {
  els.rankList.innerHTML = '';
  filteredData
    .slice()
    .sort((a, b) => (b.capacity_mw || 0) - (a.capacity_mw || 0))
    .forEach(d => {
      const isReal = d.data_source === 'real';
      const cap = d.capacity_mw ? `${d.capacity_mw} MW` : 'n/d';
      const dlt = (typeof d.delta_lst === 'number')
        ? `+${d.delta_lst.toFixed(1)} °C` : 'n/d';

      const item = document.createElement('li');
      item.className = 'mcs-dc-item' + (d.entry ? ' is-entry' : '');
      item.dataset.id = d.id;
      // o item e clicavel: damos papel de botao e suporte a teclado para acessibilidade
      item.setAttribute('role', 'button');
      item.setAttribute('tabindex', '0');
      item.setAttribute('aria-pressed', 'false');

      const tagClass = isReal ? 'mcs-dc-tag--real' : 'mcs-dc-tag--sim';
      const tagText = isReal ? 'Real' : 'Simulado';
      const cue = d.entry
        ? '<span class="mcs-dc-cue">Clique para abrir o satélite &rarr;</span>' : '';

      item.innerHTML = `
        <div class="mcs-dc-head">
          <strong>${d.city}, ${d.state}</strong>
          <span class="mcs-dc-tag ${tagClass}"><span class="mcs-dc-dot" aria-hidden="true"></span>${tagText}</span>
        </div>
        <span class="mcs-dc-op">${d.company}</span>
        <div class="mcs-dc-tel">
          <span class="mcs-dc-cell"><i>MW</i>${cap}</span>
          <span class="mcs-dc-cell"><i>&Delta;LST</i>${dlt}</span>
        </div>
        ${cue}
      `;

      const activate = () => {
        // marca este item como selecionado (estado visual de selecao)
        els.rankList.querySelectorAll('.mcs-dc-item.is-selected')
          .forEach(li => { li.classList.remove('is-selected'); li.setAttribute('aria-pressed', 'false'); });
        item.classList.add('is-selected');
        item.setAttribute('aria-pressed', 'true');

        if (d.entry && d.link) { window.location.href = d.link; return; }
        map.flyTo({ center: [d.lng, d.lat], zoom: 7 });
      };
      item.addEventListener('click', activate);
      item.addEventListener('keydown', e => {
        if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); activate(); }
      });
      els.rankList.appendChild(item);
    });
}

function translateStatus(status) {
  const labels = {
    operational: 'Operacional',
    construction: 'Em construção',
    planned: 'Planejado',
  };
  return labels[status] || status;
}
