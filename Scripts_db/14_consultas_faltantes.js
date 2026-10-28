// ------------------------------------------------------------
// CONSULTAS FALTANTES DE MONGODB
//   A. Proyecciones con find()
//   B. Temperatura promedio por zona
//   C. Sensores que superaron el límite establecido
//   D. Evolución de una variable en el tiempo (mensual y por hora)
// Ejecutar con: mongosh smartcity --file 14_consultas_faltantes.js
// ------------------------------------------------------------

print("\n=== A. PROYECCIONES CON find() ===")
var zonaEj = db.lecturas.findOne({}).sensor.zona
print("Zona de ejemplo: " + zonaEj)

print("-- Proyección de INCLUSIÓN (solo los campos elegidos):")
printjson(db.lecturas.find(
  { "sensor.zona": zonaEj },
  { _id: 0, "sensor.id": 1, "medicion.carros": 1, "medicion.temperatura": 1, timestamp: 1 }
).sort({ timestamp: -1 }).limit(3).toArray())

print("-- Proyección de EXCLUSIÓN (todo menos los campos indicados):")
printjson(db.lecturas.find(
  { "sensor.zona": zonaEj },
  { _id: 0, eventos: 0, "sensor.ubicacion": 0 }
).limit(2).toArray())


print("\n=== B. TEMPERATURA PROMEDIO POR ZONA ===")
var rB = db.lecturas.aggregate([
  { $match: { "medicion.temperatura": { $ne: null } } },
  { $group: {
      _id: "$sensor.zona",
      avg_temp: { $avg: "$medicion.temperatura" },
      max_temp: { $max: "$medicion.temperatura" },
      min_temp: { $min: "$medicion.temperatura" },
      total: { $sum: 1 }
  }},
  { $sort: { avg_temp: -1 } },
  { $limit: 15 },
  { $project: {
      _id: 0,
      zona: "$_id",
      avg_temp: { $round: ["$avg_temp", 2] },
      max_temp: 1,
      min_temp: 1,
      total: 1
  }}
]).toArray()
printjson(rB)


print("\n=== C. SENSORES QUE SUPERARON EL LÍMITE ESTABLECIDO ===")
// Mismos umbrales usados al generar la colección "alertas"
var LIM_PM25 = 50
var LIM_CONG = 70
print("Límites: PM2.5 > " + LIM_PM25 + " | congestion_score > " + LIM_CONG)
var rC = db.lecturas.aggregate([
  { $match: { $or: [
      { "medicion.pm25": { $gt: LIM_PM25 } },
      { "medicion.congestion_score": { $gt: LIM_CONG } }
  ]}},
  { $group: {
      _id: "$sensor.id",
      zona: { $first: "$sensor.zona" },
      excesos_pm25: { $sum: { $cond: [{ $gt: ["$medicion.pm25", LIM_PM25] }, 1, 0] } },
      excesos_congestion: { $sum: { $cond: [{ $gt: ["$medicion.congestion_score", LIM_CONG] }, 1, 0] } },
      max_pm25: { $max: "$medicion.pm25" },
      max_congestion: { $max: "$medicion.congestion_score" }
  }},
  { $addFields: { total_excesos: { $add: ["$excesos_pm25", "$excesos_congestion"] } } },
  { $sort: { total_excesos: -1 } },
  { $limit: 10 },
  { $project: {
      _id: 0,
      sensor: "$_id",
      zona: 1,
      excesos_pm25: 1,
      excesos_congestion: 1,
      total_excesos: 1,
      max_pm25: 1,
      max_congestion: 1
  }}
]).toArray()
printjson(rC)


print("\n=== D1. EVOLUCIÓN MENSUAL (temperatura y vehículos) ===")
var rD1 = db.lecturas.aggregate([
  { $match: { "medicion.temperatura": { $ne: null } } },
  { $group: {
      _id: { $dateToString: { format: "%Y-%m", date: "$timestamp" } },
      avg_temp: { $avg: "$medicion.temperatura" },
      avg_carros: { $avg: "$medicion.carros" },
      total: { $sum: 1 }
  }},
  { $sort: { _id: 1 } },
  { $project: {
      _id: 0,
      periodo: "$_id",
      avg_temp: { $round: ["$avg_temp", 2] },
      avg_carros: { $round: ["$avg_carros", 2] },
      total: 1
  }}
]).toArray()
printjson(rD1)

print("\n=== D2. EVOLUCIÓN POR HORA DEL DÍA (vehículos y congestión, hora UTC) ===")
var rD2 = db.lecturas.aggregate([
  { $match: { "medicion.carros": { $ne: null } } },
  { $group: {
      _id: { $hour: "$timestamp" },
      avg_carros: { $avg: "$medicion.carros" },
      avg_congestion: { $avg: "$medicion.congestion_score" },
      total: { $sum: 1 }
  }},
  { $sort: { _id: 1 } },
  { $project: {
      _id: 0,
      hora: "$_id",
      avg_carros: { $round: ["$avg_carros", 2] },
      avg_congestion: { $round: ["$avg_congestion", 2] },
      total: 1
  }}
]).toArray()
printjson(rD2)

print("\n=== FIN ===")