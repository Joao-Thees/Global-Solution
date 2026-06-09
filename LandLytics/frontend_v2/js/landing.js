// Pagina inicial: monta o globo 3D com globe.gl como elemento visual da home.
// O globo gira sozinho e pode ser arrastado; a navegacao fica nos botoes do hero.

const els = {
  globe: document.getElementById('globe'),
  loading: document.getElementById('loading'),
};

// respeita quem prefere menos animacao: nesse caso o globo nao gira sozinho
const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

let world;

// no desktop o globo ocupa a metade direita; abaixo de 900px usa a tela toda
function globeWidth() {
  return window.innerWidth > 900 ? window.innerWidth * 0.5 : window.innerWidth;
}

buildGlobe();
handleResize();

function buildGlobe() {
  world = Globe()(els.globe)
    .globeImageUrl('//unpkg.com/three-globe/example/img/earth-night.jpg')
    .bumpImageUrl('//unpkg.com/three-globe/example/img/earth-topology.png')
    .backgroundColor('#0f1417')
    .atmosphereColor('#ff9800')
    .atmosphereAltitude(0.16)
    .width(globeWidth())
    .height(window.innerHeight);

  // posicao inicial olhando para as Americas
  world.pointOfView({ lat: 24, lng: -70, altitude: 2.4 }, 0);

  const controls = world.controls();
  // zoom por roda desligado de proposito: assim a roda do mouse rola a pagina
  // em vez de aproximar o globo, mantendo a rolagem sincronizada e sem bug
  controls.enableZoom = false;
  controls.autoRotate = !reduceMotion;
  controls.autoRotateSpeed = 0.55;

  world.onGlobeReady(() => {
    els.loading.classList.add('hidden');
  });

  // rede de seguranca: se o evento de pronto nao disparar, some o loading mesmo assim
  setTimeout(() => els.loading.classList.add('hidden'), 4000);
}

// o globo nao redimensiona sozinho, entao acompanhamos a janela
function handleResize() {
  window.addEventListener('resize', () => {
    if (!world) return;
    world.width(globeWidth()).height(window.innerHeight);
  });
}
