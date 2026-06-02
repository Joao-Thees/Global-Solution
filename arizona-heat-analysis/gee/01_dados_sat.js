// =============================================================================
// Arizona Datacenter Heat Analysis - Script GEE Principal
// Adaptado de "El calor detrás de la nube" (Amenaza Roboto)
// =============================================================================

var LandsatLST = require('users/sofiaermida/landsat_smw_lst:modules/Landsat_LST.js');

// ============================================================
// 1. POLÍGONOS DOS SITES
// ============================================================

var meta_mesa = ee.Geometry.Polygon([[
  [-111.600, 33.328], [-111.581, 33.328],
  [-111.581, 33.344], [-111.600, 33.344], [-111.600, 33.328]
]]);

var google_mesa = ee.Geometry.Polygon([[
  [-111.758, 33.434], [-111.740, 33.434],
  [-111.740, 33.448], [-111.758, 33.448], [-111.758, 33.434]
]]);

var cyrusone_phoenix = ee.Geometry.Polygon([[
  [-112.018, 33.438], [-112.002, 33.438],
  [-112.002, 33.452], [-112.018, 33.452], [-112.018, 33.438]
]]);

var superstition_mall = ee.Geometry.Polygon([[
  [-111.681, 33.380], [-111.661, 33.380],
  [-111.661, 33.394], [-111.681, 33.394], [-111.681, 33.380]
]]);

var santan_mall = ee.Geometry.Polygon([[
  [-111.736, 33.306], [-111.718, 33.306],
  [-111.718, 33.322], [-111.736, 33.322], [-111.736, 33.306]
]]);

var siteDefs = [
  { id: 'meta',         poly: meta_mesa,        trat: 'dc'   },
  { id: 'google',       poly: google_mesa,       trat: 'dc'   },
  { id: 'cyrusone',     poly: cyrusone_phoenix,  trat: 'dc'   },
  { id: 'superstition', poly: superstition_mall, trat: 'mall' },
  { id: 'santan',       poly: santan_mall,       trat: 'mall' }
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

function addNDBI(img, sat) {
  var swir = sat === 'L7' ? img.select('SR_B5') : img.select('SR_B6');
  var nir  = sat === 'L7' ? img.select('SR_B4') : img.select('SR_B5');
  return img.addBands(swir.subtract(nir).divide(swir.add(nir)).rename('NDBI'));
}

// ============================================================
// 3. EXTRAÇÃO
//    - Loops JS para iterar sites/zonas/satélites (client-side)
//    - map() só para iterar imagens (server-side)
//    - ee.FeatureCollection() explícito para forçar o tipo correto
// ============================================================

var satellites = [
  { name: 'L7', startYear: 2000, endYear: 2024 },
  { name: 'L8', startYear: 2013, endYear: 2025 }
];

var allFeatures = ee.FeatureCollection([]);

siteDefs.forEach(function(site) {
  var zones  = buildZones(site.poly);
  var zNames = ['sitio', 'inner', 'outer'];
  var zGeoms = [zones.sitio, zones.inner, zones.outer];

  satellites.forEach(function(satDef) {
    var start      = ee.Date.fromYMD(satDef.startYear, 1, 1);
    var end        = ee.Date.fromYMD(satDef.endYear, 12, 31);
    var searchArea = site.poly.buffer(400);

    // LandsatLST já adiciona banda NDVI quando use_ndvi=true
    var col = LandsatLST.collection(satDef.name, start, end, searchArea, true);

    // Adiciona NDBI a cada imagem
    var satName = satDef.name;
    var colIdx  = col.map(function(img) {
      return addNDBI(img, satName);
    });

    zNames.forEach(function(zoneName, zi) {
      var zoneGeom = zGeoms[zi];
      var siteId   = site.id;
      var tratVal  = site.trat;

      // Cast explícito para FeatureCollection evita erro de tipo
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
            site: siteId,
            trat: tratVal
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

Map.centerObject(meta_mesa, 10);
siteDefs.forEach(function(s) {
  Map.addLayer(s.poly, { color: s.trat === 'dc' ? 'red' : 'blue' }, s.id);
});

print('Total de observações:', allFeatures.size());

Export.table.toDrive({
  collection:     allFeatures,
  description:    'arizona_dados_sat',
  folder:         'GEE_Arizona',
  fileNamePrefix: 'dados_sat',
  fileFormat:     'CSV',
  selectors:      ['lst', 'ndvi', 'ndbi', 'year', 'sat', 'zone', 'site', 'trat']
});
