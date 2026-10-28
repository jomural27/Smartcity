print("=== CREANDO ÍNDICES EN incidentes ===")

db.incidentes.createIndex({ "sensor_id": 1 })
db.incidentes.createIndex({ "zona": 1 })
db.incidentes.createIndex({ "tipo": 1 })
db.incidentes.createIndex({ "gravedad": 1 })
db.incidentes.createIndex({ "timestamp": -1 })

print("Índices creados:")
printjson(db.incidentes.getIndexes())