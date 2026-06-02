"""
Configuração central do projeto Arizona Datacenter Heat Analysis.
Ajuste os períodos e coordenadas aqui conforme necessário.
"""

# ──────────────────────────────────────────────────
# PERÍODOS DE ANÁLISE
# pre:   antes da construção dos principais DCs
# build: período de obras (excluído do modelo)
# ops:   DCs operacionais
# ──────────────────────────────────────────────────
PERIODS = {
    "pre":   (2000, 2015),
    "build": (2016, 2018),
    "ops":   (2019, 2025),
}

# ──────────────────────────────────────────────────
# SITES
# trat: "dc" = tratamento (datacenter) | "mall" = controle
# ──────────────────────────────────────────────────
SITES = {
    "meta": {
        "name": "Meta Mesa",
        "trat": "dc",
        "color": "#e53935",
        "center": [-111.590, 33.336],
        "bbox": [-111.600, 33.328, -111.581, 33.344],
    },
    "google": {
        "name": "Google Mesa",
        "trat": "dc",
        "color": "#fb8c00",
        "center": [-111.749, 33.441],
        "bbox": [-111.758, 33.434, -111.740, 33.448],
    },
    "cyrusone": {
        "name": "CyrusOne Phoenix",
        "trat": "dc",
        "color": "#8e24aa",
        "center": [-112.010, 33.445],
        "bbox": [-112.018, 33.438, -112.002, 33.452],
    },
    "superstition": {
        "name": "Superstition Springs Center",
        "trat": "mall",
        "color": "#1e88e5",
        "center": [-111.671, 33.387],
        "bbox": [-111.681, 33.380, -111.661, 33.394],
    },
    "santan": {
        "name": "SanTan Village",
        "trat": "mall",
        "color": "#43a047",
        "center": [-111.727, 33.314],
        "bbox": [-111.736, 33.306, -111.718, 33.322],
    },
}

# ──────────────────────────────────────────────────
# ÁREA DE ESTUDO (bbox do KML)
# ──────────────────────────────────────────────────
STUDY_BBOX = {
    "west":  -112.116,
    "east":  -111.498,
    "south":  33.222,
    "north":  33.504,
}

# ──────────────────────────────────────────────────
# CAMINHOS
# ──────────────────────────────────────────────────
DATA_DIR          = "../data/gee_exports"
RESULTS_DIR       = "../data"
HEATMAP_DIR       = "../frontend/tiles"
DADOS_SAT_CSV     = f"{DATA_DIR}/dados_sat.csv"
REFLST_CSV        = f"{DATA_DIR}/reflst.csv"
DELTA_LST_TIF     = f"{DATA_DIR}/delta_lst.tif"
RESULTS_JSON      = f"{RESULTS_DIR}/results.json"
SITES_GEOJSON     = f"{RESULTS_DIR}/sites.geojson"
HEATMAP_PNG       = f"{RESULTS_DIR}/heatmap.png"
HEATMAP_BOUNDS_JSON = f"{RESULTS_DIR}/heatmap_bounds.json"
