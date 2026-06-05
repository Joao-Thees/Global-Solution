# Arizona Datacenter Heat Analysis — V2

Análise do impacto térmico do **CyrusOne Phoenix Datacenter** sobre a temperatura superficial (LST) em relação a uma área verde adjacente, Phoenix, AZ — 2025.

Corrobora os achados de [techxplore.com/news/2026-05-centers-nearby-temperatures-degrees-phoenix](https://techxplore.com/news/2026-05-centers-nearby-temperatures-degrees-phoenix.html) usando dados Landsat via Google Earth Engine.

---

## Dados pesados (TIF) — download obrigatório

Os arquivos GeoTIFF não estão no repositório (tamanho > 100 MB). Baixe o `.zip` no link abaixo e extraia o conteúdo dentro de `data/gee_exports_v2/`:

**Download:** https://drive.google.com/drive/u/4/folders/1thUj2OWMXYefcRDSgmpq38qUsucMlkAZ

Arquivos esperados após extração:

```
data/gee_exports_v2/
├── delta_lst_v2.tif       # anomalia térmica (heatmap)
├── lst_ops_v2.tif         # LST absoluta período operacional
└── rgb_background.tif     # imagem RGB Sentinel-2 (fundo do mapa)
```

> Os CSVs (`dados_sat_v2.csv`, `reflst_v2.csv`) já estão no repositório.

---

## Instalação

```powershell
# Ativar ambiente virtual
.venv\Scripts\Activate.ps1

# Instalar dependências
pip install -r arizona-heat-analysis/python/requirements.txt
```

---

## Rodar o pipeline V2

```powershell
cd arizona-heat-analysis/python
python main.py
```

Executa em sequência:
1. `generate_report_v2.py` → `data/relatorio_v2.pdf` (LST 2025: datacenter vs área verde)
2. `generate_heatmap_v2.py` → `data/heatmap_v2.png` (mapa de calor Landsat)
3. `generate_background.py` → `data/rgb_background.png` (fundo Sentinel-2 para o mapa)

### Visualizar no navegador

Sirva a partir da raiz `arizona-heat-analysis` (NÃO de dentro de `frontend_v2`), pois o
frontend busca os dados em `../data/...`:

```powershell
cd arizona-heat-analysis
python -m http.server 8766
# Acesse: http://localhost:8766/frontend_v2/indexV2.html
```

### Ferramenta DiD (opcional)

```powershell
python arizona-heat-analysis/python/analysis_v2.py
```

Roda o modelo Diferenças-em-Diferenças (2020–2026) e atualiza `data/results_v2.json` usado pelos gráficos do frontend.

---

## Estrutura

```
arizona-heat-analysis/
├── gee_v2/                        # Scripts Google Earth Engine (JavaScript)
│   ├── 01_dados_sat.js            # extrai LST, NDVI, NDBI por site/zona/ano
│   ├── 02_reflst.js               # temperatura de referência regional
│   ├── 03_lst_image_export.js     # exporta raster de anomalia e LST ops
│   └── 04_rgb_background.js       # exporta imagem RGB Sentinel-2 (10m)
├── python/
│   ├── config.py                  # fonte única de verdade (sites, caminhos)
│   ├── main.py                    # pipeline completo (roda tudo)
│   ├── generate_report_v2.py      # relatório PDF — LST absoluta 2025
│   ├── generate_heatmap_v2.py     # mapa de calor PNG
│   ├── generate_background.py     # imagem RGB de fundo
│   ├── analysis_v2.py             # modelo DiD (ferramenta separada)
│   └── requirements.txt
├── frontend_v2/                   # Visualização web (Leaflet + Chart.js)
└── data/
    ├── gee_exports_v2/            # inputs do GEE (TIFs via Drive, CSVs no repo)
    ├── sites.geojson
    ├── results_v2.json            # output do DiD (usado pelo frontend)
    ├── heatmap_bounds_v2.json
    └── rgb_bounds.json
```

---

## Metodologia

**Relatório (V2 principal):** compara LST absoluta média de 2025 (79 cenas Landsat) entre o CyrusOne Phoenix Datacenter e a área verde adjacente demarcada por KML.

**Modelo DiD (ferramenta adicional):**

```
ihi ~ ndvi + ndbi + C(zone)*C(trat) + C(trat)*C(period)
```

- `ihi` = LST local − temperatura média regional do ano (`ref2`)
- `period`: `pre` (2020–2022) vs `ops` (2024–2026)
- Coeficiente-chave: `C(trat)[T.True]:C(period)[T.ops]`

**Dados:** Landsat 8/9 (30 m) via módulo `sofiaermida/landsat_smw_lst` no GEE.

---

## Front-End Design (FED) — documentação da entrega

Tema: **"A Interface da Missão"**. A pasta entregue da FED é `frontend_v2/`.

### Usuário e tarefa crítica
- **Usuário:** Analista de Observação da Terra de um Centro de Operações de Clima Urbano.
- **Tarefa crítica:** monitorar, via LST orbital (Landsat), o aquecimento do datacenter
  CyrusOne Phoenix frente à área verde de controle e **emitir alerta** quando a anomalia
  (Datacenter − Área verde) ultrapassa o limiar seguro configurado.
- **Conexão com a Indústria Espacial:** o produto consome dado orbital / sensoriamento remoto
  (Earth Observation) e é apresentado como **painel de missão / observação da Terra**.

### Justificativa visual
Direção visual completa (referências, análise crítica, paleta e tipografia) em
**`frontend_v2/assets/moodboard.html`**. Resumo: tema escuro para monitoramento prolongado,
laranja como cor de missão (datacenter), verde/vermelho reservados a estado (nominal/alerta),
tipografia **Inter** com numerais tabulares para alinhar as leituras de telemetria.

### Visão das telas (uma tela, regiões)
- **Mapa orbital** (`<main>`): Leaflet com fundo RGB (GEE) + camada de anomalia LST + polígonos
  dos sites; banner de **alerta crítico** sobreposto.
- **Painel de missão** (`<aside>`): telemetria ao vivo, controles (botões + formulário),
  camadas, períodos, sites, resultados do modelo, série temporal e metodologia.

### Decisões de responsividade
- Breakpoints `@media` em **1024 / 768 / 480 px**.
- ≤768 px: layout empilha — mapa no topo (50vh) e painel rolável embaixo.
- ≤480 px: fontes/margens reduzidas e alvos de toque maiores.
- `map.invalidateSize()` no `resize`/`orientationchange` (evita tiles cinza ao girar a tela).

### Decisões de acessibilidade
- Landmarks semânticos: `header / nav / main / aside / section / footer` (sem "div soup").
- Contraste mínimo **WCAG AA** (tokens `--text-muted`/`--text-dim` conferidos sobre `#0d0d0d`).
- `aria-label`/`role`/`aria-live` nos pontos dinâmicos; `<label for>` em todos os campos;
  **skip link** "Pular para o mapa"; foco visível (`:focus-visible`);
  `prefers-reduced-motion` desliga animações.
- Tabela de telemetria com `caption`, `scope` em `th` e descrição.

### Componentes (estilizados por classe, sem estilo inline no HTML)
Alerta crítico (`.alert-banner`), tabela de telemetria (`.telemetry-table`), botões
(`.btn`/`.btn-primary`/`.btn-armed`), formulário (`.mission-form`), status pills
(`.status-pill`), navegação do painel (`.panel-nav`).

### Entregáveis FED
- `integrantes.txt` (raiz) — nome completo + RM de cada integrante.
- `frontend_v2/assets/moodboard.html` — moodboard com análise crítica.

---

## Web Development (WD) — Manual de Interatividade

A interatividade está em `frontend_v2/js/`: `mainV2.js` (mapa/camadas/resultados),
`chartsV2.js` (série temporal) e `telemetryV2.js` (telemetria de tempo real / BOM).

### Telemetria em tempo real (BOM)
Ao abrir a página, a estação começa a **receber leituras simuladas do satélite a cada 2,5 s**
(`setInterval`): a tabela "Telemetria orbital ao vivo" atualiza LST do datacenter, da área verde
e o Δ de anomalia, piscando a cada varredura. O veredito alterna entre **ESTÁVEL** (verde) e
**ALERTA** (vermelho). Quando o Δ ultrapassa o limiar, a estação **emite um alerta de
emergência**: banner vermelho sobre o mapa (`role="alert"`) + um aviso (`window.alert`) único
por episódio. O estado da conexão usa `navigator.onLine` e os eventos `online`/`offline`.

### Onde clicar e o que acontece

| Controle | Ação | O que acontece na tela |
|---|---|---|
| **Forçar varredura** | clique | Dispara uma leitura imediata e reavalia o estado. |
| **Reconectar satélite** | clique | Desabilita o botão, mostra "RECONECTANDO…", e após 1,5 s (`setTimeout`) revalida a conexão e faz nova varredura. |
| **Alerta: ARMADO/DESARMADO** | clique | Liga/desliga a vigilância. Desarmar durante uma anomalia pede confirmação (`window.confirm`). |
| **Configurar limiar (formulário)** | digitar + Aplicar | Valida o número (0–20 °C); se inválido, mostra erro e `aria-invalid`; se válido, atualiza o limiar e reavalia. |
| **Mapa de calor / Imagem de fundo** | checkbox | Liga/desliga as camadas do Leaflet. |
| **Opacidade do calor** | slider | Ajusta a opacidade da camada de anomalia em tempo real. |
| **Polígono do datacenter** | hover/clique | Mostra tooltip flutuante; clique destaca o card de resultado correspondente. |

### Recursos de JavaScript demonstrados
- **DOM:** `getElementById`, `textContent`, `classList`, `setAttribute`, criação/atualização de conteúdo.
- **Eventos:** `addEventListener` para `click`, `submit`, `input`, `change`, `online`/`offline`.
- **BOM:** `setInterval`, `setTimeout`, `navigator.onLine`, `window.alert`, `window.confirm`.
- **Lógica:** validação de formulário, alternância de estado seguro→alerta, simulação de leituras.
