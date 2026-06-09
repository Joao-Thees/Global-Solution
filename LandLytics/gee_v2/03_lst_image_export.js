// =============================================================================
// Arizona Datacenter Heat Analysis v2 - Exportação Imagem Térmica (2020-2026)
// pre:  2020-2022 (antes das construções recentes)
// ops:  2024-2026 (datacenters recentes em operação)
// Satélites: L8 + L9
// =============================================================================

var LandsatLST = require('users/sofiaermida/landsat_smw_lst:modules/Landsat_LST.js');

var roi = ee.Geometry.Polygon([[
  [-112.116, 33.222],
  [-111.498, 33.222],
  [-111.498, 33.504],
  [-112.116, 33.504],
  [-112.116, 33.222]
]]);

Map.centerObject(roi, 11);

// ============================================================
// 2. COMPOSITES LST POR PERÍODO E SATÉLITE
// ============================================================

function getLSTComposite(satellite, startYear, endYear) {
  var start = ee.Date.fromYMD(startYear, 1, 1);
  var end   = ee.Date.fromYMD(endYear,   12, 31);
  var col   = LandsatLST.collection(satellite, start, end, roi, true);
  return col.select('LST').mean().clip(roi);
}

// PRÉ: 2020-2022 — L8 disponível, L9 ainda não operacional
var lst_pre_L8 = getLSTComposite('L8', 2020, 2022);
var lst_pre    = lst_pre_L8;

// OPS: 2024-2026 — L8 + L9 disponíveis
var lst_ops_L8 = getLSTComposite('L8', 2024, 2025);
var lst_ops_L9 = getLSTComposite('L9', 2024, 2026);
var lst_ops    = lst_ops_L8.add(lst_ops_L9).divide(2);

// Anomalia: OPS - PRÉ
var lst_delta = lst_ops.subtract(lst_pre).rename('delta_LST');

// ============================================================
// 3. VISUALIZAÇÃO
// ============================================================

var vizDelta = {
  min: -2, max: 6,
  palette: ['#313695','#4575b4','#74add1','#e0f3f8',
            '#ffffbf','#fee090','#fdae61','#f46d43',
            '#d73027','#a50026']
};

Map.addLayer(lst_delta, vizDelta,  'Delta LST v2 (K) OPS - PRE');
Map.addLayer(lst_pre,  {min: 295, max: 325, palette: ['blue','yellow','red']}, 'LST Pre 2020-2022',  false);
Map.addLayer(lst_ops,  {min: 295, max: 325, palette: ['blue','yellow','red']}, 'LST Ops 2024-2026',  false);

// ============================================================
// 4. EXPORTAR GeoTIFFs
// ============================================================

Export.image.toDrive({
  image:           lst_delta,
  description:     'arizona_delta_lst_v2',
  folder:          'GEE_Arizona_v2',
  fileNamePrefix:  'delta_lst_v2',
  region:          roi,
  scale:           30,
  crs:             'EPSG:4326',
  maxPixels:       1e10,
  fileFormat:      'GeoTIFF'
});

Export.image.toDrive({
  image:           lst_pre,
  description:     'arizona_lst_pre_v2',
  folder:          'GEE_Arizona_v2',
  fileNamePrefix:  'lst_pre_v2',
  region:          roi,
  scale:           30,
  crs:             'EPSG:4326',
  maxPixels:       1e10,
  fileFormat:      'GeoTIFF'
});

Export.image.toDrive({
  image:           lst_ops,
  description:     'arizona_lst_ops_v2',
  folder:          'GEE_Arizona_v2',
  fileNamePrefix:  'lst_ops_v2',
  region:          roi,
  scale:           30,
  crs:             'EPSG:4326',
  maxPixels:       1e10,
  fileFormat:      'GeoTIFF'
});

print('Exports v2 agendados. Verifique a aba Tasks no GEE.');
