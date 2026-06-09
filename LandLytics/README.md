![LandLytics Logo](Logo.png)
# LandLytics — Arizona Datacenter Heat Analysis (V2)

Análise do impacto térmico do **CyrusOne Phoenix Datacenter** sobre a temperatura superficial (LST) em relação a uma área verde adjacente, Phoenix, AZ — 2025.

Corrobora os achados de [techxplore.com/news/2026-05-centers-nearby-temperatures-degrees-phoenix](https://techxplore.com/news/2026-05-centers-nearby-temperatures-degrees-phoenix.html) usando dados Landsat via Google Earth Engine.

---

## Dados pesados (TIF) — DOWNLOAD OBRIGATÓRIO.

Os arquivos GeoTIFF não estão no repositório (tamanho > 100 MB). Baixe o `.zip` no link abaixo e extraia o conteúdo dentro de `data/gee_exports_v2/`:

**Download:** https://drive.google.com/drive/u/4/folders/1thUj2OWMXYefcRDSgmpq38qUsucMlkAZ

Arquivos esperados após extração:

```
data/gee_exports_v2/
├── delta_lst_v2.tif       # anomalia térmica (heatmap)
├── lst_ops_v2.tif         # LST absoluta período operacional
└── rgb_background.tif     # imagem RGB Sentinel-2 (fundo do mapa)
```

> Os CSVs (`dados_sat_v2.csv`, `reflst_v2.csv`) já estão no repositório, são leves e o git os suporta.

---

## Instalação

```powershell
# Ativar ambiente virtual
.venv\Scripts\Activate.ps1

# Instalar dependências
pip install -r LandLytics/python/requirements.txt
```

---

## Configurar o Mapbox (token) — obrigatório para o mapa dos EUA

O mapa dos EUA (`usa.html`) usa **Mapbox GL JS**, que exige um token de acesso. Por
segurança, o token **não fica no código nem no repositório**: ele é lido de uma
**variável de ambiente** (`os.getenv("MAPBOX_TOKEN")`) e o `python/main.py` gera o
arquivo `frontend_v2/js/config.js` (ignorado pelo git) a partir dela.

**Passo a passo:**

1. Crie uma conta grátis em **https://www.mapbox.com**.
2. Acesse **Account → Tokens**. Copie o **Default public token** (começa com `pk.`)
   ou crie um novo. Recomendado: em **URL restrictions**, adicione `http://localhost:8766`
   (e o domínio do seu deploy, se houver) — assim o token só funciona nos seus endereços.
3. Defina a variável de ambiente `MAPBOX_TOKEN`:

   ```powershell
   # Windows PowerShell (vale para a sessão atual do terminal)
   $env:MAPBOX_TOKEN = "pk....seu_token_aqui"
   ```
   ```bash
   # Linux / macOS
   export MAPBOX_TOKEN="pk....seu_token_aqui"
   ```
   > Em **deploy**, configure `MAPBOX_TOKEN` nas *environment variables* da plataforma.

4. Gere o `config.js` (é o **passo 0** do pipeline):

   ```powershell
   python LandLytics/python/main.py
   ```
   Isso cria `frontend_v2/js/config.js` com o token. (Modelo do formato em
   `frontend_v2/js/config.example.js`.) Se a variável não estiver definida, o `main.py`
   avisa e o mapa exibe uma mensagem pedindo a configuração — o resto do site funciona.

> 🔒 O `config.js` está no `.gitignore` e **nunca** é versionado. Só o
> `config.example.js` (com placeholder) vai para o repositório.

---

## Rodar o pipeline V2

```powershell
cd LandLytics/python
python main.py
```

`main.py` é o **ponto de entrada único** e o **motor analítico** do projeto.
Executa em sequência:
1. `analysis_v2.py` → `data/results_v2.json` (modelo DiD: decompõe a anomalia térmica)
2. `generate_report_v2.py` → `data/relatorio_v2.pdf` (LST 2025: datacenter vs área verde)
3. `generate_heatmap_v2.py` → `data/heatmap_v2.png` (mapa de calor Landsat)
4. `generate_background.py` → `data/rgb_background.png` (fundo Sentinel-2 para o mapa)

### Visualizar no navegador

> ⚠️ Rode `python main.py` **antes** de abrir o frontend — o PDF e os PNGs
> (`heatmap_v2.png`, `rgb_background.png`) não vêm no repositório, são gerados
> pelo pipeline.

Sirva a partir da raiz `LandLytics` (NÃO de dentro de `frontend_v2`), pois o
frontend busca os dados em `../data/...`:

```powershell
cd LandLytics
python -m http.server 8766
# Acesse: http://localhost:8766/frontend_v2/indexV2.html
```

### Rodar só o modelo DiD (opcional)

O `python main.py` já roda o modelo. Para executar **apenas** o motor analítico
(sem gerar PDF/mapas), o `analysis_v2.py` continua funcionando isolado:

```powershell
python LandLytics/python/analysis_v2.py
```

Roda o modelo Diferenças-em-Diferenças (2020–2026) e atualiza `data/results_v2.json` usado pelos gráficos do frontend.

---

## Estrutura

```
LandLytics/
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
├── frontend_v2/                   # Visualização web (3 telas)
│   ├── index.html                 # tela inicial: globo 3D (globe.gl)
│   ├── usa.html                   # mapa dos EUA (Mapbox) + impactos
│   ├── indexV2.html               # painel de missão (Leaflet)
│   ├── css/                       # tokens.css (design system), landing.css, mission-header.css, usa.css, usa-sidebar.css, styleV2.css
│   ├── js/                        # landing.js, mission-header.js, usa.js, mainV2.js, telemetryV2.js
│   ├── data/                      # datacenters_usa.json (5 data centers)
│   └── assets/                    # Logo.png, moodboard.html e referências visuais
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

## Computational Thinking with Python (CTWP) — documentação da entrega

Tema: **o "Centro de Controle" da missão** — o motor analítico em Python que
ingere os dados orbitais (LST do Landsat via GEE), aplica as regras de análise e
gera o relatório e os resultados do modelo. Conexão espacial: **Observação da
Terra (Earth Observation)**.

### Problema analítico
A partir de cenas Landsat de Phoenix (AZ), medir **quanto o datacenter CyrusOne
Phoenix aquece a superfície** em relação a uma área verde de controle e estimar
**quanto desse calor vem da operação dos servidores** (e não de mudança de
cobertura do solo ou da tendência regional).

### Como executar
```powershell
cd LandLytics/python
python main.py
```
`main.py` é o **motor analítico** (ponto de entrada único): roda o modelo DiD
(`analysis_v2.py`) e depois gera relatório, mapa de calor e fundo RGB.

### Formato dos dados consumidos
`data/gee_exports_v2/dados_sat_v2.csv` — uma linha por cena Landsat / zona / ano:

| coluna | tipo | descrição |
|---|---|---|
| `lst`  | float | temperatura de superfície (Kelvin) |
| `ndvi` | float | índice de vegetação |
| `ndbi` | float | índice de área construída |
| `year` | int   | ano da cena |
| `sat`  | texto | satélite (L8 / L9) |
| `zone` | texto | sitio / inner / outer |
| `site` | texto | cyrusone / area_verde |
| `trat` | texto | dc (tratamento) / green (controle) |

`reflst_v2.csv` — `year, sat, ref2` (temperatura de referência regional do ano).

### Onde cada requisito da CTWP aparece
- **Estruturas de dados:** dicionários e tuplas em `config.py` (`SITES`,
  `PERIODS_V2`), dicts de saída em `analysis_v2.py` e `generate_report_v2.py`,
  listas em todo o código.
- **Modularização (funções):** cada script separa ingestão / análise / exibição
  (ex.: `load_data` → `run_model` → `export_results`).
- **Lógica (laços e condicionais):** `for`/list comprehensions e `if/elif/else`
  (ex.: `classify_period`, decomposição da anomalia).
- **Tratamento de erros:** `try/except` na leitura de CSV/TIF e na escrita de
  arquivos, evitando interrupções bruscas por dados inválidos.
- **Uso de IA:** documentado em [`python/prompts.md`](python/prompts.md), com as
  perguntas feitas ao Claude e a explicação da lógica (IHI e DiD) que a equipe domina.

### Conceitos-chave (resumo; detalhes em `python/prompts.md`)
- **IHI** = `LST_local − ref2`: o quanto um ponto está mais quente que a média
  regional do mesmo ano.
- **DiD (Diferenças-em-Diferenças):** isola o efeito causal da operação comparando
  `(datacenter depois − antes) − (área verde depois − antes)`.

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

### Telas e fluxo do site
O site tem três telas, todas em `frontend_v2/`, num fluxo simples da apresentação até o dado real:

1. **Tela inicial — globo 3D** (`index.html`): portal de entrada. No topo, um **header de
   mission control** (faixa de telemetria com relógio de Brasília ao vivo, status do sistema,
   modo operacional e banner de alerta térmico). Na coluna direita, um globo (globe.gl) gira como
   elemento visual da Terra; na coluna esquerda, um texto em cards explica o impacto ambiental e os
   botões levam às outras telas. Estrutura semântica `header / main / article`, com o título da
   análise como heading do artigo.
2. **Mapa dos EUA** (`usa.html`): mapa Mapbox com 5 data centers reais (localização verificada em
   catálogos públicos), filtro por estado, métricas, ranking e cards de impacto. Estrutura
   `header / nav / aside / main / section / article`.
3. **Painel de missão** (`indexV2.html`): a tela analítica principal, com dados reais de satélite.
   Abre com uma **tela de carregamento da missão** (texto "Carregando missão de análise de LST via
   Landsat 8 / 9", exibida por um tempo mínimo via `setTimeout` no `mainV2.js`).
   - **Mapa orbital** (`<main>`): Leaflet com fundo RGB (GEE) + camada de anomalia LST + polígonos
     dos sites; banner de **alerta crítico** sobreposto.
   - **Painel de missão** (`<aside>`): telemetria ao vivo, controles (botões + formulário),
     camadas, períodos, sites e metodologia.

**Fluxo:** `index.html` (globo) → `usa.html` (mapa dos EUA) → clique em Phoenix → `indexV2.html` (satélite).

### Decisões de responsividade
- **Painel de missão** (`indexV2.html`): breakpoints `@media` em **1024 / 768 / 480 px**.
  ≤768 px empilha (mapa no topo, painel rolável embaixo); ≤480 px reduz fontes/margens e aumenta
  alvos de toque; `map.invalidateSize()` no `resize`/`orientationchange` evita tiles cinza.
- **Tela inicial — globo** (`index.html`): duas colunas (texto à esquerda, globo à direita) no
  desktop; **≤900 px** empilha e o globo vira um fundo discreto em largura total; ajustes finos
  **≤480 px**. O globo é redimensionado no `resize`.
- **Mapa dos EUA** (`usa.html`): breakpoints em **1024 / 768 / 480 px**; ≤768 px o painel lateral
  desce abaixo do mapa.

### Decisões de acessibilidade
- Landmarks semânticos: `header / nav / main / aside / section / footer` (sem "div soup").
- Contraste mínimo **WCAG AA** (tokens `--text-muted`/`--text-dim` conferidos sobre `#0d0d0d`).
- `aria-label`/`role`/`aria-live` nos pontos dinâmicos; `<label for>` em todos os campos;
  **skip link** "Pular para o mapa"; foco visível (`:focus-visible`);
  `prefers-reduced-motion` desliga animações.
- Tabela de telemetria com `caption`, `scope` em `th` e descrição.
- **Telas novas:** logo com `alt` descritivo (sem imagem sem `alt`); métricas, ranking e stats como
  listas (`<ul>`/`<li>`); itens de ranking e marcadores com `role="button"`, `tabindex` e ativação
  por teclado (Enter/Espaço); skip link em cada tela; sem estilo inline no HTML.

### Tokens (design system)
A paleta e a forma ficam centralizadas em **`frontend_v2/css/tokens.css`** (fonte única,
carregada antes do CSS de cada tela). Os CSS de tela só guardam tokens próprios (ex.: `--panel-w`,
`--radius` do painel V2) e os componentes (`mission-header.css`, `usa-sidebar.css`) herdam as cores
da paleta central via `var(--accent)`, `var(--danger)` etc. — sem hex duplicado.

### Componentes (estilizados por classe, sem estilo inline no HTML)
Alerta crítico (`.alert-banner`), tabela de telemetria (`.telemetry-table`), botões
(`.btn`/`.btn-primary`/`.btn-armed`), formulário (`.mission-form`), status pills
(`.status-pill`), navegação do painel (`.panel-nav`), header de missão (`.mc-*`) e console
nacional (`.mcs-*`). Sem estilo inline nas telas (e o moodboard usa classes utilitárias).

### Entregáveis FED
- `integrantes.txt` (raiz) — nome completo + RM de cada integrante.
- `frontend_v2/assets/moodboard.html` — moodboard com análise crítica.

---

## Web Development (WD) — Manual de Interatividade

A interatividade está em `frontend_v2/js/`: na **tela inicial** `landing.js` (globo 3D) e
`mission-header.js` (relógio de Brasília ao vivo + medição do header), no **mapa dos EUA**
`usa.js` (Mapbox, filtros, ranking) e no **painel de missão** `mainV2.js`
(mapa Leaflet / camadas / opacidade) e `telemetryV2.js` (telemetria de tempo real / BOM).

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
| **Polígono do datacenter** | hover | Mostra uma tooltip flutuante que segue o mouse sobre a área do CyrusOne. |

### Telas de entrada (globo e mapa): onde clicar e o que acontece

**Tela inicial — globo 3D (`index.html`)**

| Controle | Ação | O que acontece na tela |
|---|---|---|
| **Globo** | arrastar | Gira o globo (controles do globe.gl); ele também gira sozinho. |
| **Botão "Explorar o mapa dos EUA"** | clique | Leva ao mapa dos EUA (`usa.html`). |
| **Botão "Ver análise de Phoenix"** | clique | Abre o painel de missão (`indexV2.html`). |

**Mapa dos EUA (`usa.html`)**

| Controle | Ação | O que acontece na tela |
|---|---|---|
| **Filtrar por estado** | selecionar | Filtra marcadores, métricas e ranking pelo estado escolhido. |
| **Mostrar marcadores** | checkbox | Liga/desliga os marcadores do mapa. |
| **Marcador de data center** | clique | Abre um popup com operador, status e capacidade. |
| **Marcador de Phoenix** | clique | Abre o painel de missão (`indexV2.html`). |
| **Item do ranking** | clique/Enter | Centraliza o mapa no data center (Phoenix abre o painel). |
| **Resetar** | clique | Limpa o filtro e volta à visão nacional. |

### Recursos de JavaScript demonstrados
- **DOM:** `getElementById`, `textContent`, `classList`, `setAttribute`, criação/atualização de conteúdo.
- **Eventos:** `addEventListener` para `click`, `submit`, `input`, `change`, `online`/`offline`.
- **BOM:** `setInterval`, `setTimeout`, `navigator.onLine`, `window.alert`, `window.confirm`.
- **Lógica:** validação de formulário, alternância de estado seguro→alerta, simulação de leituras.
- **Telas de entrada:** `fetch` de JSON, `createElement`/`appendChild` para marcadores e ranking,
  `addEventListener` (`click`, `change`, `keydown`, `mousemove`, `resize`), navegação por
  `window.location`, e as bibliotecas de mapa globe.gl e Mapbox GL JS.
