"""
Arizona Datacenter Heat Analysis v2 - Geração da Imagem RGB de Fundo
Converte o GeoTIFF RGB exportado do GEE (rgb_background.tif) em PNG
para uso como camada de fundo no frontend, substituindo o tile do Esri.
"""

import json
from pathlib import Path

import numpy as np
import rasterio
from PIL import Image

import sys
sys.path.insert(0, str(Path(__file__).parent))
import config


def load_rgb(tif_path: str):
    try:
        with rasterio.open(tif_path) as src:
            # GEE exporta na ordem SR_B4(R), SR_B3(G), SR_B2(B)
            r = src.read(1).astype(float)
            g = src.read(2).astype(float)
            b = src.read(3).astype(float)
            bounds = src.bounds
            nodata = src.nodata

            if nodata is not None:
                r[r == nodata] = np.nan
                g[g == nodata] = np.nan
                b[b == nodata] = np.nan
    except Exception as e:
        raise RuntimeError(f"Erro ao ler GeoTIFF RGB '{tif_path}': {e}") from e

    return r, g, b, bounds


def normalize_band(band: np.ndarray, p_low=2, p_high=98) -> np.ndarray:
    valid = band[~np.isnan(band)]
    vmin  = np.percentile(valid, p_low)
    vmax  = np.percentile(valid, p_high)
    norm  = np.clip((band - vmin) / (vmax - vmin + 1e-9), 0, 1)
    norm[np.isnan(band)] = 0
    return (norm * 255).astype(np.uint8)


def render_png(r, g, b, out_path: str):
    r_u8 = normalize_band(r)
    g_u8 = normalize_band(g)
    b_u8 = normalize_band(b)

    rgb_array = np.stack([r_u8, g_u8, b_u8], axis=2)
    img = Image.fromarray(rgb_array, mode="RGB")
    try:
        img.save(out_path)
    except OSError as e:
        print(f"[ERRO] Não foi possível salvar o PNG em {out_path}: {e}")
        return
    print(f"[OK] RGB PNG salvo: {out_path}  ({rgb_array.shape[1]}x{rgb_array.shape[0]}px)")


def save_bounds(bounds, out_path: str):
    obj = {
        "south": bounds.bottom,
        "west":  bounds.left,
        "north": bounds.top,
        "east":  bounds.right,
    }
    with open(out_path, "w") as f:
        json.dump(obj, f, indent=2)
    print(f"[OK] Bounds RGB salvos: {out_path}")


def main():
    print("=" * 60)
    print("  Gerando imagem RGB de fundo (v2)...")
    print("=" * 60)

    tif_path = Path(config.RGB_BACKGROUND_TIF)
    if not tif_path.exists():
        print(f"[ERRO] Arquivo não encontrado: {tif_path}")
        return

    print(f"\n>> Lendo GeoTIFF RGB: {tif_path}")
    try:
        r, g, b, bounds = load_rgb(str(tif_path))
    except RuntimeError as e:
        print(f"[ERRO] {e}")
        return
    print(f"   Dimensões: {r.shape[1]}x{r.shape[0]}px")

    out_png    = config.RGB_PNG
    out_bounds = config.RGB_BOUNDS_JSON

    Path(out_png).parent.mkdir(parents=True, exist_ok=True)
    render_png(r, g, b, out_png)
    save_bounds(bounds, out_bounds)

    print("\n  Pronto. Imagem RGB disponível para o frontend.")


if __name__ == "__main__":
    main()
