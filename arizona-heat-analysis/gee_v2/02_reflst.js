// =============================================================================
// Arizona Datacenter Heat Analysis v2 - Referência Regional LST (2020-2026)
// =============================================================================

var LandsatLST = require('users/sofiaermida/landsat_smw_lst:modules/Landsat_LST.js');

var study_center = ee.Geometry.Point([-111.807, 33.353]);
var roi = study_center.buffer(5000);

Map.centerObject(roi, 11);
Map.addLayer(roi, {color: 'blue'}, 'Buffer 5km (referencia regional)');

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
          reducer:   ee.Reducer.mean(),
          geometry:  roi,
          scale:     30,
          maxPixels: 1e9
        }).get('LST'),
        null
      );

      return ee.Feature(null, { year: y, sat: satellite, ref2: mean });
    })
  );
}

var ref_L8 = getAnnualRefLST('L8', 2020, 2025);
var ref_L9 = getAnnualRefLST('L9', 2022, 2026);

var ref_all = ref_L8.merge(ref_L9)
  .filter(ee.Filter.notNull(['ref2']));

print('reflst v2 - total features:', ref_all.size());

Export.table.toDrive({
  collection:     ref_all,
  description:    'arizona_reflst_v2',
  folder:         'GEE_Arizona_v2',
  fileNamePrefix: 'reflst_v2',
  fileFormat:     'CSV',
  selectors:      ['year', 'sat', 'ref2']
});
