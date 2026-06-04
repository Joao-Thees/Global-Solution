// =============================================================================
// Arizona Datacenter Heat Analysis v2 - Dados Satelitais (2020-2026)
// Sites: CyrusOne Phoenix (DC) e Área Verde adjacente
// Satélites: L8 (2020-2025) + L9 (2022-2026)
// =============================================================================

var LandsatLST = require('users/sofiaermida/landsat_smw_lst:modules/Landsat_LST.js');

// ============================================================
// 1. POLÍGONOS — extraídos do KML CYRIUSPHOENIXDATACENTER.kml
// ============================================================

var cyrusone_phoenix = ee.Geometry.Polygon([[
  [-111.8807, 33.2724],
  [-111.8843, 33.2722],
  [-111.8844, 33.2714],
  [-111.8844, 33.2653],
  [-111.8805, 33.2655],
  [-111.8807, 33.2724]
]]);

var area_verde = ee.Geometry.Polygon([[
  [-111.8933, 33.2722],
  [-111.8933, 33.2673],
  [-111.8892, 33.2673],
  [-111.8893, 33.2723],
  [-111.8933, 33.2722]
]]);

var siteDefs = [
  { id: 'cyrusone',   poly: cyrusone_phoenix, trat: 'dc'    },
  { id: 'area_verde', poly: area_verde,        trat: 'green' }
];

// ============================================================
// 2. FUNÇÕES AUXILIARES
// ============================================================

function buildZones(poly) {
  var center = poly.centroid(1);
  var buf150 = center.buffer(150);
  var buf300 = center.buffer(300);
  return {
    sitio: poly,
    inner: buf150.difference(poly, 1),
    outer: buf300.difference(buf150, 1)
  };
}

function addNDBI(img) {
  var swir = img.select('SR_B6');
  var nir  = img.select('SR_B5');
  return img.addBands(swir.subtract(nir).divide(swir.add(nir)).rename('NDBI'));
}

// ============================================================
// 3. EXTRAÇÃO — L8 (2020-2025) e L9 (2022-2026)
// ============================================================

var satellites = [
  { name: 'L8', startYear: 2020, endYear: 2025 },
  { name: 'L9', startYear: 2022, endYear: 2026 }
];

var allFeatures = ee.FeatureCollection([]);

siteDefs.forEach(function(site) {
  var zones  = buildZones(site.poly);
  var zNames = ['sitio', 'inner', 'outer'];
  var zGeoms = [zones.sitio, zones.inner, zones.outer];

  satellites.forEach(function(satDef) {
    var start   = ee.Date.fromYMD(satDef.startYear, 1, 1);
    var end     = ee.Date.fromYMD(satDef.endYear,   12, 31);
    var satName = satDef.name;

    var col = LandsatLST.collection(satName, start, end, site.poly.buffer(400), true);

    var colIdx = col.map(function(img) {
      return addNDBI(img);
    });

    zNames.forEach(function(zoneName, zi) {
      var zoneGeom = zGeoms[zi];

      var fc = ee.FeatureCollection(
        colIdx.map(function(img) {
          var stats = img.select(['LST', 'NDVI', 'NDBI'])
            .reduceRegion({
              reducer:   ee.Reducer.mean(),
              geometry:  zoneGeom,
              scale:     30,
              maxPixels: 1e9
            });

          return ee.Feature(null, {
            lst:  stats.get('LST'),
            ndvi: stats.get('NDVI'),
            ndbi: stats.get('NDBI'),
            year: img.date().get('year'),
            sat:  satName,
            zone: zoneName,
            site: site.id,
            trat: site.trat
          });
        })
      ).filter(ee.Filter.notNull(['lst', 'ndvi', 'ndbi']));

      allFeatures = allFeatures.merge(fc);
    });
  });
});

// ============================================================
// 4. VISUALIZAR E EXPORTAR
// ============================================================

Map.centerObject(cyrusone_phoenix, 14);
Map.addLayer(cyrusone_phoenix, { color: 'FF6600' }, 'CyrusOne Phoenix (DC)');
Map.addLayer(area_verde,       { color: '00AA00' }, 'Area Verde');

print('Total de observacoes:', allFeatures.size());

Export.table.toDrive({
  collection:     allFeatures,
  description:    'arizona_dados_sat_v2',
  folder:         'GEE_Arizona_v2',
  fileNamePrefix: 'dados_sat_v2',
  fileFormat:     'CSV',
  selectors:      ['lst', 'ndvi', 'ndbi', 'year', 'sat', 'zone', 'site', 'trat']
});
