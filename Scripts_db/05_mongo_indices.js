// Índices en lecturas
db.lecturas.createIndex({ "sensor.id": 1 })
db.lecturas.createIndex({ "sensor.zona": 1 })
db.lecturas.createIndex({ "timestamp": -1 })
db.lecturas.createIndex({ "sensor.id": 1, "timestamp": -1 })

// Índices en alertas
db.alertas.createIndex({ "sensor_id": 1 })
db.alertas.createIndex({ "zona": 1 })
db.alertas.createIndex({ "tipo_alerta": 1 })
db.alertas.createIndex({ "timestamp": -1 })

// Ver los índices creados
print("=== Índices en lecturas ===")
printjson(db.lecturas.getIndexes())

print("\n=== Índices en alertas ===")
printjson(db.alertas.getIndexes())

print("\n=== Conteo final ===")
print("Documentos en lecturas: " + db.lecturas.countDocuments())
print("Documentos en alertas: " + db.alertas.countDocuments())