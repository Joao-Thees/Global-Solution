// =============================================================================
// Arizona Datacenter Heat Analysis - Referência Regional LST
// Adaptado de gee_reflst.js (Amenaza Roboto)
//
// Computa temperatura média regional anual (buffer 5km do centróide da área)
// Exporta: reflst.csv  →  usado para calcular IHI = lst - ref2
// =============================================================================

var LandsatLST = require('users/sofiaermida/landsat_smw_lst:modules/Landsat_LST.js');

// ============================================================
// 1. GEOMETRIA: centróide da área de estudo + buffer 5km
//    (centro aproximado da área marcada no KML do Arizona)
// ============================================================
var study_center = ee.Geometry.Point([-111.807, 33.353]);
var roi = study_center.buffer(5000);

Map.centerObject(roi, 11);
Map.addLayer(roi, {color: 'blue'}, 'Buffer 5km (referência regional)');

// ============================================================
// 2. FUNÇÃO: LST anual médio regional
// ============================================================
function getAnnualRefLST(satellite, startYear, endYear) {
  var years = ee.List.sequence(startYear, endYear);

  return ee.FeatureCollection(
    years.map(function(y) {
      y = ee.Number(y);
      var start = ee.Date.fromYMD(y, 1, 1);
      var end   = ee.Date.fromYMD(y, 12, 31);

      var col   = LandsatLST.collection(satellite, start, end, roi, true);
      var count = col.size();

      var mean = ee.Algorithms.If(
        count.gt(0),
        col.select('LST').mean().reduceRegion({
          reducer: ee.Reducer.mean(),
          geometry: roi,
          scale: 30,
          maxPixels: 1e9
        }).get('LST'),
        null
      );

      return ee.Feature(null, {
        year: y,
        sat:  satellite,
        ref2: mean
      });
    })
  );
}

// ============================================================
// 3. CALCULAR E EXPORTAR
// ============================================================
var ref_L7 = getAnnualRefLST('L7', 2000, 2024);
var ref_L8 = getAnnualRefLST('L8', 2014, 2025);

var ref_all = ref_L7.merge(ref_L8)
  .filter(ee.Filter.notNull(['ref2']));

print('reflst - total features:', ref_all.size());
print('Dados:', ref_all);

Export.table.toDrive({
  collection: ref_all,
  description: 'arizona_reflst',
  folder: 'GEE_Arizona',
  fileNamePrefix: 'reflst',
  fileFormat: 'CSV',
  selectors: ['year', 'sat', 'ref2']
});
