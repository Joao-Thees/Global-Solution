// =============================================================================
// Arizona Datacenter Heat Analysis - Exportação de Imagem Térmica
//
// Exporta imagens raster GeoTIFF de LST (temperatura de superfície) para
// geração do mapa de calor visual no frontend.
// Gera dois composites: período PRÉ (2000-2015) e OPS (2019-2025)
// O frontend exibe a ANOMALIA: LST_ops - LST_pre (delta temperatura)
// =============================================================================

var LandsatLST = require('users/sofiaermida/landsat_smw_lst:modules/Landsat_LST.js');

// ============================================================
// 1. ÁREA DE INTERESSE (bbox do KML do Arizona)
// ============================================================
var roi = ee.Geometry.Polygon([[
  [-112.116, 33.222],
  [-111.498, 33.222],
  [-111.498, 33.504],
  [-112.116, 33.504],
  [-112.116, 33.222]
]]);

Map.centerObject(roi, 11);

// ============================================================
// 2. FUNÇÃO: composite LST médio para um período
// ============================================================
function getLSTComposite(satellite, startYear, endYear) {
  var start = ee.Date.fromYMD(startYear, 1, 1);
  var end   = ee.Date.fromYMD(endYear,   12, 31);
  var col   = LandsatLST.collection(satellite, start, end, roi, true);
  return col.select('LST').mean().clip(roi);
}

// ============================================================
// 3. COMPOSITES PRÉ E OPS
// ============================================================
// Pré-operação: ambos satélites disponíveis a partir de 2013
var lst_pre_L7  = getLSTComposite('L7', 2000, 2015);
var lst_ops_L7  = getLSTComposite('L7', 2019, 2024);
var lst_ops_L8  = getLSTComposite('L8', 2019, 2025);

// Média entre satélites disponíveis por período
var lst_pre  = lst_pre_L7;  // apenas L7 disponível antes de 2013
var lst_ops  = lst_ops_L7.add(lst_ops_L8).divide(2);

// Anomalia: OPS - PRÉ (quanto aumentou a temperatura)
var lst_delta = lst_ops.subtract(lst_pre).rename('delta_LST');

// ============================================================
// 4. VISUALIZAÇÃO NO GEE (preview)
// ============================================================
var vizParams = {
  min: -2, max: 6,
  palette: ['#313695','#4575b4','#74add1','#e0f3f8',
            '#ffffbf','#fee090','#fdae61','#f46d43',
            '#d73027','#a50026']
};
Map.addLayer(lst_delta, vizParams, 'Delta LST (°K) OPS - PRE');
Map.addLayer(lst_pre,   {min: 295, max: 320, palette: ['blue','yellow','red']}, 'LST Pré', false);
Map.addLayer(lst_ops,   {min: 295, max: 320, palette: ['blue','yellow','red']}, 'LST Ops', false);

// ============================================================
// 5. EXPORTAR GeoTIFFs para Python processar
// ============================================================
Export.image.toDrive({
  image: lst_delta,
  description: 'arizona_delta_lst',
  folder: 'GEE_Arizona',
  fileNamePrefix: 'delta_lst',
  region: roi,
  scale: 30,
  crs: 'EPSG:4326',
  maxPixels: 1e10,
  fileFormat: 'GeoTIFF'
});

Export.image.toDrive({
  image: lst_pre,
  description: 'arizona_lst_pre',
  folder: 'GEE_Arizona',
  fileNamePrefix: 'lst_pre',
  region: roi,
  scale: 30,
  crs: 'EPSG:4326',
  maxPixels: 1e10,
  fileFormat: 'GeoTIFF'
});

Export.image.toDrive({
  image: lst_ops,
  description: 'arizona_lst_ops',
  folder: 'GEE_Arizona',
  fileNamePrefix: 'lst_ops',
  region: roi,
  scale: 30,
  crs: 'EPSG:4326',
  maxPixels: 1e10,
  fileFormat: 'GeoTIFF'
});

print('Exports agendados. Verifique a aba Tasks no GEE.');
