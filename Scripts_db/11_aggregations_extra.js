
//AGREGACION SOBRE INCIDENTES

print("\n=== INCIDENTES POR CATEGORÍA (query #8 obligatoria) ===")
var r1 = db.incidentes.aggregate([
    { $group: {
        _id: { tipo: "$tipo", gravedad: "$gravedad" },
        total: { $sum: 1 },
        tiempo_resp_prom: { $avg: "$tiempo_respuesta_min" },
        vehiculos_prom: { $avg: "$vehiculos_involucrados" }
    }},
    { $sort: { total: -1 } },
    { $limit: 15 }
]).toArray()
printjson(r1)

print("\n=== INCIDENTES POR ZONA ===")
var r2 = db.incidentes.aggregate([
    { $group: {
        _id: "$zona",
        total_incidentes: { $sum: 1 },
        criticos: { $sum: { $cond: [{ $eq: ["$gravedad", "critica"] }, 1, 0] } },
        tiempo_prom: { $avg: "$tiempo_respuesta_min" }
    }},
    { $sort: { total_incidentes: -1 } },
    { $limit: 10 }
]).toArray()
printjson(r2)

print("\n=== PROMEDIO POR TIPO DE SENSOR (query #7 corregida) ===")
var r3 = db.lecturas.aggregate([
    { $group: {
        _id: "$sensor.tipo",
        total: { $sum: 1 },
        avg_pm25: { $avg: "$medicion.pm25" },
        avg_carros: { $avg: "$medicion.carros" }
    }}
]).toArray()
printjson(r3)

print("\n=== TIPOS DE INCIDENTES (frecuencia) ===")
var r4 = db.incidentes.aggregate([
    { $group: {
        _id: "$tipo",
        total: { $sum: 1 }
    }},
    { $sort: { total: -1 } }
]).toArray()
printjson(r4)

print("\n=== FIN ===")