print("=== 1. AGREGAR sensor.tipo A TODOS LOS DOCUMENTOS ===")

// Los que tienen "CDMX" en el id → calidad_aire
var r1 = db.lecturas.updateMany(
    { "sensor.id": { $regex: "^CDMX_" } },
    { $set: { "sensor.tipo": "calidad_aire" } }
)
print("Documentos marcados como calidad_aire: " + r1.modifiedCount)

// Los demás → trafico
var r2 = db.lecturas.updateMany(
    { "sensor.id": { $not: { $regex: "^CDMX_" } } },
    { $set: { "sensor.tipo": "trafico" } }
)
print("Documentos marcados como trafico: " + r2.modifiedCount)

print("\n=== 2. VERIFICAR DISTRIBUCIÓN ===")
var r3 = db.lecturas.aggregate([
    { $group: { _id: "$sensor.tipo", total: { $sum: 1 } } },
    { $sort: { total: -1 } }
]).toArray()
printjson(r3)

print("\n=== 3. CREAR ÍNDICE EN sensor.tipo ===")
db.lecturas.createIndex({ "sensor.tipo": 1 })
print("Índice creado en sensor.tipo")

print("\n=== FIN ===")