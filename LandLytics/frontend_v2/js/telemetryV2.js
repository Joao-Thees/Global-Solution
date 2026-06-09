/* Telemetria da estação — recebe as "leituras do satélite" e decide se está
   tudo normal ou se precisa soltar o alerta de emergência.

   Os números não vêm de satélite de verdade: parto da LST média de 2025 do
   relatório (datacenter 310.19 K / área verde 306.37 K) e somo um ruidinho
   aleatório a cada varredura só pra dar a sensação de tempo real.

   É aqui que está o que o WD pede: setInterval/setTimeout, navigator.onLine,
   eventos online/offline, validação de formulário e manipulação do DOM. */
(function () {
  "use strict";

  // valores de base (Kelvin) tirados do relatório v2
  const DC_BASE_K    = 310.19;
  const GREEN_BASE_K = 306.37;
  const SCAN_MS      = 2500;  // intervalo entre uma leitura e outra
  const HISTERESE    = 0.5;   // folga pra não ficar ligando/desligando o alerta

  const state = {
    thresholdC: 4.5,   // bate com o value do input no HTML
    armed:      true,
    scans:      0,
    inDanger:   false,
    timer:      null,
  };

  const $ = (id) => document.getElementById(id);
  const el = {
    dcK: $("tlm-dc-k"),
    dcC: $("tlm-dc-c"),
    greenK: $("tlm-green-k"),
    greenC: $("tlm-green-c"),
    deltaK: $("tlm-delta-k"),
    deltaC: $("tlm-delta-c"),
    status: $("thermal-status"),
    link: $("link-status"),
    scan: $("scan-count"),
    thrLabel: $("threshold-label"),
    thrInput: $("threshold-input"),
    thrError: $("threshold-error"),
    banner: $("alert-banner"),
    alertText: $("alert-text"),
    btnScan: $("btn-scan"),
    btnReconnect: $("btn-reconnect"),
    btnArm: $("btn-arm"),
    btnDismiss: $("alert-dismiss"),
    form: $("threshold-form"),
  };

  // se não estou na página da telemetria, paro por aqui
  if (!el.status || !el.dcK) return;

  const kToC = (k) => k - 273.15;
  // ruído pequeno só pra dar vida aos números. Antes estava grande demais
  // (±0.9 / ±0.6) e o Δ ficava cruzando o limiar toda hora.
  const noise = (amp) => (Math.random() - 0.5) * 2 * amp;
  const fmt = (n, d = 2) => n.toFixed(d);

  function flash(cell) {
    if (!cell) return;
    cell.classList.remove("tlm-flash");
    void cell.offsetWidth; // reinicia a animação
    cell.classList.add("tlm-flash");
  }

  // uma varredura = uma leitura nova
  function scan() {
    const dcK    = DC_BASE_K    + noise(0.30);
    const greenK = GREEN_BASE_K + noise(0.20);
    const deltaC = kToC(dcK) - kToC(greenK); // diferença em °C (mesmo valor em K)

    el.dcK.textContent    = fmt(dcK, 2);
    el.dcC.textContent    = fmt(kToC(dcK), 2);
    el.greenK.textContent = fmt(greenK, 2);
    el.greenC.textContent = fmt(kToC(greenK), 2);
    el.deltaK.textContent = (deltaC >= 0 ? "+" : "") + fmt(deltaC, 2);
    el.deltaC.textContent = (deltaC >= 0 ? "+" : "") + fmt(deltaC, 2);
    flash(el.deltaK); // pisca só o delta, pra não ficar a tabela inteira piscando

    state.scans += 1;
    el.scan.textContent = String(state.scans);

    evaluate(deltaC);
  }

  // decide entre estável / alerta usando histerese, pra não flicar
  function evaluate(deltaC) {
    if (!state.armed) {
      setStatus("DESARMADO", false);
      hideBanner();
      state.inDanger = false;
      return;
    }

    if (!state.inDanger && deltaC > state.thresholdC) {
      // acabou de passar do limiar -> avisa UMA vez
      state.inDanger = true;
      setStatus("ALERTA", true);
      showBanner(
        `EMERGÊNCIA TÉRMICA: anomalia de +${fmt(deltaC, 2)} °C passou do limiar ` +
        `seguro de +${fmt(state.thresholdC, 1)} °C no CyrusOne Phoenix.`
      );
      // setTimeout pra pintar o banner antes de travar a tela com o alert
      setTimeout(() => {
        window.alert(
          "⚠ ALERTA DE EMERGÊNCIA\n\n" +
          "A anomalia térmica do datacenter passou do limiar seguro.\n" +
          "Confira o painel de telemetria."
        );
      }, 0);
    } else if (state.inDanger && deltaC < state.thresholdC - HISTERESE) {
      // caiu bem abaixo do limiar -> normalizou
      state.inDanger = false;
      setStatus("ESTÁVEL", false);
      hideBanner();
    } else if (state.inDanger) {
      // continua acima, mas sem reabrir o popup
      setStatus("ALERTA", true);
    } else {
      setStatus("ESTÁVEL", false);
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
  }

  // estado da conexão (navigator.onLine + eventos online/offline)
  function refreshLink() {
    const online = navigator.onLine;
    el.link.textContent = online ? "ONLINE" : "OFFLINE";
    el.link.classList.toggle("status-ok", online);
    el.link.classList.toggle("status-danger", !online);
  }
  window.addEventListener("online", refreshLink);
  window.addEventListener("offline", refreshLink);

  // botões
  el.btnScan && el.btnScan.addEventListener("click", scan);

  el.btnDismiss && el.btnDismiss.addEventListener("click", hideBanner);

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
    // se for desarmar no meio de uma anomalia, pede confirmação
    if (state.armed && state.inDanger) {
      const ok = window.confirm(
        "Desarmar o alerta durante uma anomalia ativa?\n" +
        "A estação vai parar de sinalizar a emergência."
      );
      if (!ok) return;
    }
    state.armed = !state.armed;
    el.btnArm.setAttribute("aria-pressed", String(state.armed));
    el.btnArm.textContent = state.armed ? "Alerta: ARMADO" : "Alerta: DESARMADO";
    scan();
  });

  // formulário: valida o limiar antes de aplicar
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
    // se baixou o limiar pra debaixo do delta atual, deixa reavaliar do zero
    state.inDanger = false;
    scan();
  });

  // começo
  refreshLink();
  scan();
  state.timer = setInterval(scan, SCAN_MS);
})();
