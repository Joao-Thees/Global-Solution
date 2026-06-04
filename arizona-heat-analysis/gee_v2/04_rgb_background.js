// =============================================================================
// Arizona Datacenter Heat Analysis v2 - Imagem RGB de Fundo (Sentinel-2, 10m)
//
// Usa Sentinel-2 SR (10m) em vez de Landsat 9 (30m) para maior resolução.
// Revisita a cada 5 dias → composite muito mais limpo que Landsat.
// Alinhado temporalmente com o heatmap v2 (ops 2024-2026).
// =============================================================================

var roi = ee.Geometry.Polygon([[
  [-112.116, 33.222],
  [-111.498, 33.222],
  [-111.498, 33.504],
  [-112.116, 33.504],
  [-112.116, 33.222]
]]);

Map.centerObject(roi, 11);

// ============================================================
// 1. MÁSCARA DE NUVENS — usa banda QA60 do Sentinel-2
// ============================================================

function maskS2clouds(img) {
  var qa    = img.select('QA60');
  var cloud = 1 << 10;  // bit 10 = nuvem opaca
  var cirro = 1 << 11;  // bit 11 = cirrus
  var mask  = qa.bitwiseAnd(cloud).eq(0)
               .and(qa.bitwiseAnd(cirro).eq(0));
  return img.updateMask(mask);
}

// ============================================================
// 2. COMPOSIÇÃO RGB — Sentinel-2 SR (2024-2025)
// Bandas: B4=Red (10m), B3=Green (10m), B2=Blue (10m)
// ============================================================

var col_S2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(roi)
  .filterDate('2024-01-01', '2025-12-31')
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
  .map(maskS2clouds)
  .map(function(img) {
    return img.select(['B4', 'B3', 'B2'])
              .divide(10000)  // escala S2: DN / 10000 = reflectância
              .copyProperties(img, img.propertyNames());
  });

var rgb = col_S2.median().clip(roi);

print('Imagens Sentinel-2 disponiveis:', col_S2.size());

// ============================================================
// 3. VISUALIZAÇÃO PRÉVIA NO GEE
// ============================================================

Map.addLayer(rgb, { min: 0.0, max: 0.3 }, 'RGB S2 2024-2025 (fundo 10m)');

// ============================================================
// 4. EXPORTAR GeoTIFF RGB a 10m
// Será convertido em PNG pelo generate_background.py
// ============================================================

Export.image.toDrive({
  image:          rgb,
  description:    'arizona_rgb_background_s2',
  folder:         'GEE_Arizona_v2',
  fileNamePrefix: 'rgb_background',
  region:         roi,
  scale:          10,
  crs:            'EPSG:4326',
  maxPixels:      1e13,
  fileFormat:     'GeoTIFF'
});

print('Export Sentinel-2 RGB agendado. Verifique a aba Tasks no GEE.');
