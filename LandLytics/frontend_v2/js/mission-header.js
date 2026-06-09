/* Relógio ao vivo da faixa de telemetria do header de mission control.
   Mostra o horário de Brasília (America/Sao_Paulo) em HH:MM:SS, 24h, tabular. */
(function () {
  "use strict";

  var el = document.getElementById("mc-utc");
  if (!el) return;

  var fmt = new Intl.DateTimeFormat("pt-BR", {
    timeZone: "America/Sao_Paulo",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false
  });

  function tick() {
    el.textContent = fmt.format(new Date());
  }

  tick();
  setInterval(tick, 1000);

  /* --- alinha o globo 3D logo abaixo do header ---
     Mede a altura real do header e a expoe em --header-h (usada pelo
     #globe e .vignette no landing.css). Refaz o globo quando muda. */
  var header = document.querySelector(".mc-header");
  if (header) {
    var syncHeaderHeight = function () {
      var h = Math.round(header.getBoundingClientRect().height);
      var cur = parseInt(
        document.documentElement.style.getPropertyValue("--header-h"),
        10
      );
      if (h !== cur) {
        document.documentElement.style.setProperty("--header-h", h + "px");
        // forca o globe.gl a reajustar ao novo tamanho do contêiner
        window.dispatchEvent(new Event("resize"));
      }
    };

    syncHeaderHeight();
    window.addEventListener("load", syncHeaderHeight);
    if (window.ResizeObserver) {
      new ResizeObserver(syncHeaderHeight).observe(header);
    }
  }
})();
