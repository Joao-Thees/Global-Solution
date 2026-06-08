"""
Arizona Datacenter Heat Analysis v2 - Geração do Mapa de Calor
Converte delta_lst_v2.tif (anomalia: ops 2024-2026 vs pre 2020-2022) em PNG.
Resultado: heatmap_v2.png + heatmap_bounds_v2.json (usado pelo Leaflet no frontend_v2)
"""

import json
import sys
from pathlib import Path

import numpy as np
import matplotlib
import matplotlib.image
import matplotlib.colors as mcolors
from matplotlib.colors import LinearSegmentedColormap

sys.path.insert(0, str(Path(__file__).parent))
import config

HEAT_COLORS = [
    "#313695",
    "#4575b4",
    "#74add1",
    "#abd9e9",
    "#e0f3f8",
    "#ffffbf",
    "#fee090",
    "#fdae61",
    "#f46d43",
    "#d73027",
    "#a50026",
]

VMIN = -2.0
VMAX =  6.0


def build_colormap():
    return LinearSegmentedColormap.from_list(
        "heat_az_v2",
        list(zip(np.linspace(0, 1, len(HEAT_COLORS)), HEAT_COLORS))
    )


def generate_from_geotiff(tif_path: str):
    import rasterio
    try:
        with rasterio.open(tif_path) as src:
            data   = src.read(1).astype(float)
            nodata = src.nodata
            bounds = src.bounds

            if nodata is not None:
                data[data == nodata] = np.nan

            valid = data[~np.isnan(data)]
            if len(valid) == 0:
                raise ValueError("GeoTIFF não contém pixels válidos (todos são NoData).")
            p2, p98 = np.nanpercentile(valid, 2), np.nanpercentile(valid, 98)
            vmin = max(VMIN, p2)
            vmax = min(VMAX, p98)
    except Exception as e:
        raise RuntimeError(f"Erro ao ler GeoTIFF '{tif_path}': {e}") from e

    return data, bounds, vmin, vmax


def generate_synthetic(bounds):
    """Fallback: gera mapa sintético para demonstração quando o TIF está ausente/corrompido."""
    w, s, e, n = bounds.west, bounds.south, bounds.east, bounds.north
    cols = 1600
    rows = int(cols * (n - s) / (e - w))
    lons = np.linspace(w, e, cols)
    lats = np.linspace(n, s, rows)
    lon_grid, lat_grid = np.meshgrid(lons, lats)

    data = np.zeros((rows, cols))
    for site_id, site in config.SITES.items():
        cx, cy = site["center"]
        dist = np.sqrt((lon_grid - cx) ** 2 + (lat_grid - cy) ** 2) * 111_000
        intensity = 4.5 if site["trat"] == "dc" else 0.8
        sigma     = 1500 if site["trat"] == "dc" else 800
        data += intensity * np.exp(-(dist ** 2) / (2 * sigma ** 2))

    rng = np.random.default_rng(42)
    data += rng.normal(0, 0.3, data.shape)
    return data, VMIN, VMAX


def render_png(data, vmin, vmax, out_path: str):
    cmap = build_colormap()
    norm = mcolors.Normalize(vmin=vmin, vmax=vmax)

    rgba      = cmap(norm(data))
    alpha_raw = np.abs(data) / (vmax - vmin + 1e-9)
    alpha_raw = np.clip(alpha_raw * 2.5, 0.0, 1.0)
    alpha_raw[np.isnan(data)] = 0.0
    rgba[:, :, 3] = alpha_raw

    try:
        matplotlib.image.imsave(out_path, rgba)
    except OSError as e:
        print(f"[ERRO] Não foi possível salvar o PNG em {out_path}: {e}")
        sys.exit(1)
    print(f"[OK] Heatmap v2 PNG salvo: {out_path}  ({data.shape[1]}x{data.shape[0]}px)")


def save_bounds(bounds, out_path: str):
    obj = {
        "south": bounds.bottom,
        "west":  bounds.left,
        "north": bounds.top,
        "east":  bounds.right,
    }
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(obj, f, indent=2)
    print(f"[OK] Bounds v2 salvos: {out_path}")


def main():
    print("=" * 60)
    print("  Gerando mapa de calor v2 (2020-2026)...")
    print("=" * 60)

    tif_path     = Path(config.DELTA_LST_TIF_V2)
    use_synthetic = False

    if tif_path.exists():
        print(f"\n>> Lendo GeoTIFF v2: {tif_path}")
        try:
            data, bounds, vmin, vmax = generate_from_geotiff(str(tif_path))
            print(f"   Dimensões: {data.shape}  |  Range: [{vmin:.2f}, {vmax:.2f}] K")
        except RuntimeError as e:
            print(f"[AVISO] {e}")
            print("   Usando mapa de demonstração (sintético) como fallback...")
            use_synthetic = True
    else:
        print(f"\n>> delta_lst_v2.tif não encontrado em {tif_path}")
        print("   Gerando mapa de demonstração (sintético)...")
        use_synthetic = True

    if use_synthetic:
        from types import SimpleNamespace
        b = config.STUDY_BBOX
        # rasterio usa left/right/bottom/top — mesmos nomes que save_bounds espera
        bounds = SimpleNamespace(
            left=b["west"], right=b["east"],
            bottom=b["south"], top=b["north"],
            west=b["west"],  east=b["east"],
            south=b["south"], north=b["north"]
        )
        data, vmin, vmax = generate_synthetic(bounds)

    out_png    = config.HEATMAP_PNG_V2
    out_bounds = config.HEATMAP_BOUNDS_JSON_V2

    Path(out_png).parent.mkdir(parents=True, exist_ok=True)
    render_png(data, vmin, vmax, out_png)
    save_bounds(bounds, out_bounds)

    print("\n  Pronto. Abra http://localhost:8766/frontend_v2/indexV2.html no navegador. ")


if __name__ == "__main__":
    main()
