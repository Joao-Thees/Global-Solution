/* Arizona Heat Analysis V2 — Telemetria de missão (WD: DOM + Eventos + BOM)
   --------------------------------------------------------------------------
   Simula a chegada de leituras de temperatura de superfície (LST) do satélite
   em tempo real (setInterval), alterna o estado seguro→alerta e dispara um
   alerta de emergência quando a anomalia Datacenter − Área verde ultrapassa o
   limiar configurado. Demonstra: setInterval/setTimeout, navigator.onLine,
   eventos online/offline, validação de formulário e manipulação do DOM.

   Valores-base vêm da LST absoluta de 2025 (relatório v2):
     Datacenter ≈ 310.19 K (37.04 °C) | Área verde ≈ 306.37 K (33.22 °C)
*/
(function () {
  "use strict";

  // ── Constantes de simulação ───────────────────────────────────────────
  const DC_BASE_K    = 310.19;
  const GREEN_BASE_K = 306.37;
  const SCAN_MS      = 2500;

  // ── Estado da missão ──────────────────────────────────────────────────
  const state = {
    thresholdC: 4.0,
    armed:      true,
    scans:      0,
    inDanger:   false,
    alertedOnce:false,
    timer:      null,
  };

  // ── Atalhos de DOM ────────────────────────────────────────────────────
  const $ = (id) => document.getElementById(id);
  const el = {
    dcK:    $("tlm-dc-k"),    dcC:    $("tlm-dc-c"),
    greenK: $("tlm-green-k"), greenC: $("tlm-green-c"),
    deltaK: $("tlm-delta-k"), deltaC: $("tlm-delta-c"),
    status: $("thermal-status"),
    link:   $("link-status"),
    scan:   $("scan-count"),
    thrLabel: $("threshold-label"),
    thrInput: $("threshold-input"),
    thrError: $("threshold-error"),
    banner: $("alert-banner"),
    alertText: $("alert-text"),
    btnScan: $("btn-scan"),
    btnReconnect: $("btn-reconnect"),
    btnArm: $("btn-arm"),
    form: $("threshold-form"),
  };

  // Se a página não tem os elementos de telemetria, não faz nada.
  if (!el.status || !el.dcK) return;

  // ── Utilitários ───────────────────────────────────────────────────────
  const kToC = (k) => k - 273.15;
  const noise = (amp) => (Math.random() - 0.5) * 2 * amp;
  const fmt = (n, d = 2) => n.toFixed(d);

  function flash(cells) {
    cells.forEach((c) => {
      if (!c) return;
      c.classList.remove("tlm-flash");
      // força reflow para reiniciar a animação
      void c.offsetWidth;
      c.classList.add("tlm-flash");
    });
  }

  // ── Uma leitura/varredura ─────────────────────────────────────────────
  function scan() {
    const dcK    = DC_BASE_K    + noise(0.9);
    const greenK = GREEN_BASE_K + noise(0.6);
    const deltaC = kToC(dcK) - kToC(greenK); // diferença em °C (= em K)

    el.dcK.textContent    = fmt(dcK, 2);
    el.dcC.textContent    = fmt(kToC(dcK), 2);
    el.greenK.textContent = fmt(greenK, 2);
    el.greenC.textContent = fmt(kToC(greenK), 2);
    el.deltaK.textContent = (deltaC >= 0 ? "+" : "") + fmt(deltaC, 2);
    el.deltaC.textContent = (deltaC >= 0 ? "+" : "") + fmt(deltaC, 2);
    flash([el.dcK, el.greenK, el.deltaK]);

    state.scans += 1;
    el.scan.textContent = String(state.scans);

    evaluate(deltaC);
  }

  // ── Avalia seguro vs alerta ───────────────────────────────────────────
  function evaluate(deltaC) {
    const danger = state.armed && deltaC > state.thresholdC;

    if (danger) {
      setStatus("ALERTA", true);
      showBanner(
        `EMERGÊNCIA TÉRMICA: anomalia de +${fmt(deltaC, 2)} °C excede o limiar ` +
        `seguro de +${fmt(state.thresholdC, 1)} °C no CyrusOne Phoenix.`
      );
      // Alerta de emergência único por episódio (não bloqueia a cada varredura).
      if (!state.inDanger && !state.alertedOnce) {
        state.alertedOnce = true;
        // setTimeout para não travar o ciclo de render antes de pintar o banner.
        setTimeout(() => {
          window.alert(
            "⚠ ALERTA DE EMERGÊNCIA\n\n" +
            "A anomalia térmica do datacenter ultrapassou o limiar seguro.\n" +
            "Verifique o painel de telemetria."
          );
        }, 0);
      }
      state.inDanger = true;
    } else {
      setStatus(state.armed ? "ESTÁVEL" : "DESARMADO", false);
      hideBanner();
      state.inDanger = false;
    }
  }

  function setStatus(text, danger) {
    el.status.textContent = text;
    el.status.classList.toggle("status-danger", danger);
    el.status.classList.toggle("status-ok", !danger);
  }

  function showBanner(msg) {
    if (!el.banner) return;
    el.alertText.textContent = msg;
    el.banner.hidden = false;
  }
  function hideBanner() {
    if (el.banner) el.banner.hidden = true;
    state.alertedOnce = false; // permite novo alerta no próximo episódio
  }

  // ── Estado da conexão (BOM: navigator + eventos online/offline) ───────
  function refreshLink() {
    const online = navigator.onLine;
    el.link.textContent = online ? "ONLINE" : "OFFLINE";
    el.link.classList.toggle("status-ok", online);
    el.link.classList.toggle("status-danger", !online);
  }
  window.addEventListener("online", refreshLink);
  window.addEventListener("offline", refreshLink);

  // ── Botões ────────────────────────────────────────────────────────────
  el.btnScan && el.btnScan.addEventListener("click", scan);

  el.btnReconnect && el.btnReconnect.addEventListener("click", () => {
    el.btnReconnect.disabled = true;
    el.link.textContent = "RECONECTANDO…";
    el.link.classList.remove("status-ok", "status-danger");
    setTimeout(() => {
      refreshLink();
      el.btnReconnect.disabled = false;
      scan();
    }, 1500);
  });

  el.btnArm && el.btnArm.addEventListener("click", () => {
    // Confirmação (BOM: confirm) ao desarmar durante uma anomalia ativa.
    if (state.armed && state.inDanger) {
      const ok = window.confirm(
        "Desarmar o alerta durante uma anomalia ativa?\n" +
        "A estação deixará de sinalizar a emergência."
      );
      if (!ok) return;
    }
    state.armed = !state.armed;
    el.btnArm.setAttribute("aria-pressed", String(state.armed));
    el.btnArm.textContent = state.armed ? "Alerta: ARMADO" : "Alerta: DESARMADO";
    scan();
  });

  // ── Formulário: validação do limiar ──────────────────────────────────
  el.form && el.form.addEventListener("submit", (e) => {
    e.preventDefault();
    const raw = el.thrInput.value.trim().replace(",", ".");
    const val = Number(raw);
    let err = "";

    if (raw === "" || Number.isNaN(val)) err = "Informe um número válido.";
    else if (val < 0 || val > 20)        err = "O limiar deve estar entre 0 e 20 °C.";

    if (err) {
      el.thrInput.setAttribute("aria-invalid", "true");
      el.thrError.textContent = err;
      el.thrError.hidden = false;
      el.thrInput.focus();
      return;
    }

    el.thrInput.removeAttribute("aria-invalid");
    el.thrError.hidden = true;
    state.thresholdC = val;
    el.thrLabel.textContent = "+" + fmt(val, 1);
    scan(); // reavalia imediatamente com o novo limiar
  });

  // ── Início ────────────────────────────────────────────────────────────
  refreshLink();
  scan();
  state.timer = setInterval(scan, SCAN_MS);
})();
