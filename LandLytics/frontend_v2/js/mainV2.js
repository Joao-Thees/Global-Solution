/* Mapa do painel V2 — monta o Leaflet, joga por cima a imagem RGB do GEE,
   o mapa de calor (anomalia LST) e os polígonos dos dois sites.
   Diferente do V1: o fundo é a imagem do GEE (Landsat 9, 2024-25) no lugar do
   tile do Esri, e o heatmap é o delta pré(2020-22) x ops(2024-26). */

const DATA = '../data';

// mapa sem camada base; quem faz o fundo é a imagem do GEE logo abaixo
const map = L.map('map', {
  center: [33.270, -111.889],
  zoom: 14,
  zoomControl: false,
  layers: [],
});

L.control.zoom({ position: 'bottomright' }).addTo(map);

// quando giro a tela ou mudo o tamanho no celular o Leaflet às vezes deixa os
// tiles cinzas; esse invalidateSize com um respiro de 200ms resolve
let resizeTimer = null;
function refreshMapSize() {
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => map.invalidateSize(), 200);
}
window.addEventListener('resize', refreshMapSize);
window.addEventListener('orientationchange', refreshMapSize);


// imagem RGB de fundo (vem do GEE)
let rgbLayer = null;
let rgbVisible = true;

async function loadRGBBackground() {
  try {
    const res = await fetch(`${DATA}/rgb_bounds.json`);
    if (!res.ok) throw new Error('rgb_bounds.json não encontrado');
    const b = await res.json();
    const bounds = [[b.south, b.west], [b.north, b.east]];

    rgbLayer = L.imageOverlay(`${DATA}/rgb_background.png`, bounds, {
      opacity: 1.0,
      interactive: false,
      className: 'rgb-background',
    });
    rgbLayer.addTo(map);
  } catch (e) {
    console.warn('[V2] RGB de fundo indisponível:', e.message);
  }
}


// mapa de calor (a anomalia de temperatura)
let heatLayer = null;
let heatVisible = true;
let heatOpacity = 0.85;

async function loadHeatmap() {
  try {
    const res = await fetch(`${DATA}/heatmap_bounds_v2.json`);
    if (!res.ok) throw new Error('heatmap_bounds_v2.json não encontrado');
    const b = await res.json();
    const bounds = [[b.south, b.west], [b.north, b.east]];

    heatLayer = L.imageOverlay(`${DATA}/heatmap_v2.png`, bounds, {
      opacity: heatOpacity,
      className: 'heatmap-sharp',
      interactive: false,
    });
    if (heatVisible) heatLayer.addTo(map);

    // deixa o PNG do heatmap menos borrado quando dou zoom
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
    console.warn('[V2] Heatmap v2 indisponível:', e.message);
    console.info('[V2] Rode python generate_heatmap_v2.py pra gerar o heatmap_v2.png');
  }
}


// polígonos dos sites (datacenter e área verde)
const SITE_STYLES = {
  dc:    { weight: 2, dashArray: null,  fillOpacity: 0.15 },
  green: { weight: 2, dashArray: '5,5', fillOpacity: 0.12 },
  bbox:  { weight: 1, dashArray: '6,3', fillOpacity: 0.04 },
};

async function loadSites() {
  try {
    const res = await fetch(`${DATA}/sites.geojson`);
    if (!res.ok) throw new Error('sites.geojson não encontrado');
    const data = await res.json();

    L.geoJSON(data, {
      style: f => ({
        color: f.properties.color,
        fillColor: f.properties.color,
        ...(SITE_STYLES[f.properties.trat] || SITE_STYLES.bbox),
      }),
      onEachFeature: (f, layer) => {
        if (f.properties.trat === 'bbox') return;

        // no datacenter eu uso uma tooltip que segue o mouse; nos outros a
        // tooltip padrão do Leaflet já basta
        const tip = document.getElementById('map-tip');
        if (f.properties.id === 'cyrusone') {
          layer.on('mouseover', () => { tip.style.display = 'block'; });
          layer.on('mousemove', e => {
            tip.style.left = (e.originalEvent.clientX + 14) + 'px';
            tip.style.top  = (e.originalEvent.clientY - 36) + 'px';
          });
          layer.on('mouseout', () => { tip.style.display = 'none'; });
        } else {
          layer.bindTooltip(f.properties.name, {
            className: 'site-tooltip', sticky: true, direction: 'top', offset: [0, -4],
          });
        }
      },
    }).addTo(map);
  } catch (e) {
    console.warn('[V2] Sites não carregados:', e.message);
  }
}


// controles do painel: liga/desliga camadas e ajusta a opacidade do calor
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
  const opVal = document.getElementById('opacity-val');
  opSlider.addEventListener('input', e => {
    heatOpacity = e.target.value / 100;
    opVal.textContent = e.target.value + '%';
    heatLayer?.setOpacity(heatOpacity);
  });
}


// arranca tudo
function hideLoading() {
  const el = document.getElementById('loading');
  if (!el) return;
  el.classList.add('hidden');
  setTimeout(() => el.remove(), 500);
}

async function init() {
  try {
    await loadRGBBackground();
    await Promise.all([loadSites(), loadHeatmap()]);
    setupControls();
  } catch (e) {
    console.error('[V2] Erro na inicialização:', e);
  } finally {
    hideLoading();
  }
}

init();
