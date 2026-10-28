
//ESTAS SON LAS CONSULTAS DE MONGO este archivo se ejecuta en powershell

print("\n=== 1. LECTURAS DE UN SENSOR ESPECÍFICO ===")
var sensorEjemplo = db.lecturas.findOne({}).sensor.id
print("Sensor de ejemplo: " + sensorEjemplo)
var r1 = db.lecturas.aggregate([
  { $match: { "sensor.id": sensorEjemplo } },
  { $limit: 3 },
  { $project: {
      _id: 0,
      sensor: "$sensor.id",
      zona: "$sensor.zona",
      pm25: "$medicion.pm25",
      carros: "$medicion.carros",
      timestamp: 1
  }}
]).toArray()
printjson(r1)

print("\n=== 2. LECTURAS EN RANGO DE FECHAS ===")
// Rango dinámico: primeros 30 días de datos que existan realmente
var primera = db.lecturas.find({}, { _id: 0, timestamp: 1 }).sort({ timestamp: 1 }).limit(1).toArray()[0].timestamp
var ultima = db.lecturas.find({}, { _id: 0, timestamp: 1 }).sort({ timestamp: -1 }).limit(1).toArray()[0].timestamp
print("Datos disponibles desde " + primera.toISOString() + " hasta " + ultima.toISOString())
var fechaIni = primera
var fechaFin = new Date(primera.getTime() + 30 * 24 * 60 * 60 * 1000)
var filtroFecha = { timestamp: { $gte: fechaIni, $lte: fechaFin } }
print("Rango consultado: " + fechaIni.toISOString() + " a " + fechaFin.toISOString())
print("Total en rango: " + db.lecturas.countDocuments(filtroFecha))
print("-- Top 5 zonas en ese rango:")
printjson(db.lecturas.aggregate([
  { $match: filtroFecha },
  { $group: { _id: "$sensor.zona", total: { $sum: 1 } } },
  { $sort: { total: -1 } },
  { $limit: 5 }
]).toArray())
// Verificar que usa el índice de timestamp
var plan = db.lecturas.find(filtroFecha).explain("executionStats")
print("Plan: " + plan.queryPlanner.winningPlan.stage + " / " + (plan.queryPlanner.winningPlan.inputStage || {}).stage +
      " | docs examinados: " + plan.executionStats.totalDocsExamined +
      " | devueltos: " + plan.executionStats.nReturned)

print("\n=== 3. VALORES MÁXIMOS Y MÍNIMOS ===")
// $max y $min ignoran los null automáticamente
var r3 = db.lecturas.aggregate([
  { $group: {
      _id: null,
      max_pm25: { $max: "$medicion.pm25" },
      min_pm25: { $min: "$medicion.pm25" },
      max_carros: { $max: "$medicion.carros" },
      min_carros: { $min: "$medicion.carros" },
      max_temp: { $max: "$medicion.temperatura" },
      min_temp: { $min: "$medicion.temperatura" },
      max_congestion: { $max: "$medicion.congestion_score" },
      min_congestion: { $min: "$medicion.congestion_score" },
      total: { $sum: 1 }
  }},
  { $project: { _id: 0 } }
]).toArray()
printjson(r3)
print("-- Sensor y zona con el máximo de vehículos:")
printjson(db.lecturas.find(
  { "medicion.carros": { $ne: null } },
  { _id: 0, "sensor.id": 1, "sensor.zona": 1, "medicion.carros": 1, timestamp: 1 }
).sort({ "medicion.carros": -1 }).limit(1).toArray())
print("-- Sensor y zona con el máximo de PM2.5:")
printjson(db.lecturas.find(
  { "medicion.pm25": { $ne: null } },
  { _id: 0, "sensor.id": 1, "sensor.zona": 1, "medicion.pm25": 1, timestamp: 1 }
).sort({ "medicion.pm25": -1 }).limit(1).toArray())

print("\n=== 4. EVENTOS CRÍTICOS (PM2.5 > 100) ===")
var r4 = db.lecturas.aggregate([
  { $match: { "medicion.pm25": { $gt: 100 } } },
  { $group: {
      _id: "$sensor.zona",
      total_eventos: { $sum: 1 },
      max_pm25: { $max: "$medicion.pm25" }
  }},
  { $sort: { total_eventos: -1 } },
  { $limit: 10 }
]).toArray()
printjson(r4)

print("\n=== 5. ALERTAS POR ZONA GEOGRÁFICA ===")
var r5 = db.alertas.aggregate([
  { $group: {
      _id: "$zona",
      total_alertas: { $sum: 1 },
      criticos: { $sum: { $cond: [{ $eq: ["$nivel", "critico"] }, 1, 0] } },
      tipos: { $addToSet: "$tipo_alerta" }
  }},
  { $sort: { total_alertas: -1 } },
  { $limit: 10 }
]).toArray()
printjson(r5)

print("\n=== 6. PROMEDIO DE MEDICIONES POR ZONA ===")
var r6 = db.lecturas.aggregate([
  { $match: { "medicion.pm25": { $ne: null } } },
  { $group: {
      _id: "$sensor.zona",
      avg_pm25: { $avg: "$medicion.pm25" },
      avg_carros: { $avg: "$medicion.carros" },
      total: { $sum: 1 }
  }},
  { $sort: { avg_pm25: -1 } },
  { $limit: 10 },
  { $project: {
      _id: 0,
      zona: "$_id",
      avg_pm25: { $round: ["$avg_pm25", 2] },
      avg_carros: { $round: ["$avg_carros", 2] },
      total: 1
  }}
]).toArray()
printjson(r6)

print("\n=== 7. PROMEDIO POR TIPO DE SENSOR ===")
var r7 = db.lecturas.aggregate([
  { $group: {
      _id: "$sensor.tipo",
      total: { $sum: 1 },
      avg_pm25: { $avg: "$medicion.pm25" },
      avg_carros: { $avg: "$medicion.carros" }
  }}
]).toArray()
printjson(r7)

print("\n=== 8. INCIDENTES POR CATEGORÍA ===")
var r8 = db.incidentes.aggregate([
  { $group: {
      _id: "$tipo",
      total: { $sum: 1 },
      criticos: { $sum: { $cond: [{ $eq: ["$gravedad", "critica"] }, 1, 0] } },
      tiempo_resp_prom: { $avg: "$tiempo_respuesta_min" }
  }},
  { $sort: { total: -1 } },
  { $project: {
      _id: 0,
      tipo: "$_id",
      total: 1,
      criticos: 1,
      tiempo_resp_prom: { $round: ["$tiempo_resp_prom", 2] }
  }}
]).toArray()
printjson(r8)

print("\n=== 9. SENSORES CON MÁS LECTURAS ===")
var r9 = db.lecturas.aggregate([
  { $group: {
      _id: "$sensor.id",
      zona: { $first: "$sensor.zona" },
      total_lecturas: { $sum: 1 },
      avg_pm25: { $avg: "$medicion.pm25" }
  }},
  { $sort: { total_lecturas: -1 } },
  { $limit: 10 },
  { $project: {
      _id: 0,
      sensor: "$_id",
      zona: 1,
      total_lecturas: 1,
      avg_pm25: { $round: ["$avg_pm25", 2] }
  }}
]).toArray()
printjson(r9)

print("\n=== 10. FILTROS MÚLTIPLES ===")
// Tráfico en día laboral con muchos vehículos y congestión alta (usa el índice sensor.tipo)
var r10 = db.lecturas.aggregate([
  { $match: {
      "sensor.tipo": "trafico",
      "medicion.carros": { $gt: 100 },
      "medicion.congestion_score": { $gt: 70 },
      "eventos.es_fin_semana": false,
      timestamp: { $gte: new Date("2026-01-01"), $lt: new Date("2026-04-01") }
  }},
  { $group: {
      _id: "$sensor.zona",
      total: { $sum: 1 },
      avg_carros: { $avg: "$medicion.carros" },
      avg_congestion: { $avg: "$medicion.congestion_score" }
  }},
  { $sort: { total: -1 } },
  { $limit: 10 },
  { $project: {
      _id: 0,
      zona: "$_id",
      total: 1,
      avg_carros: { $round: ["$avg_carros", 2] },
      avg_congestion: { $round: ["$avg_congestion", 2] }
  }}
]).toArray()
printjson(r10)

print("\n=== FIN DE LAS 10 CONSULTAS ===")