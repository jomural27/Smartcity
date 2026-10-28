print("=== ESTADO FINAL DE MONGO ===")
print("Colecciones: " + db.getCollectionNames().join(", "))
print("")
print("lecturas: " + db.lecturas.countDocuments({}))
print("alertas: " + db.alertas.countDocuments({}))
print("incidentes: " + db.incidentes.countDocuments({}))
print("eventos: " + db.eventos.countDocuments({}))
print("")
print("Documentos con sensor.tipo: " + db.lecturas.countDocuments({ "sensor.tipo": { $exists: true } }))
print("")
print("=== DISTRIBUCIÓN POR TIPO DE SENSOR ===")
printjson(db.lecturas.aggregate([
    { $group: { _id: "$sensor.tipo", total: { $sum: 1 } } }
]).toArray())

print("\n=== DISTRIBUCIÓN DE INCIDENTES POR GRAVEDAD ===")
printjson(db.incidentes.aggregate([
    { $group: { _id: "$gravedad", total: { $sum: 1 } } },
    { $sort: { total: -1 } }
]).toArray())