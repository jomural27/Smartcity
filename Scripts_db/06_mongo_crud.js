
print("=== INSERT ONE ===")
db.lecturas.insertOne({
  sensor: { id: "TEST-001", zona: "Test", ubicacion: { lat: 0, lon: 0 } },
  medicion: { pm25: 10, carros: 5 },
  eventos: { accidente: false, es_fin_semana: false },
  timestamp: new Date()
})

print("=== FIND ONE ===")
printjson(db.lecturas.findOne({ "sensor.id": "TEST-001" }))

print("=== UPDATE ONE ===")
db.lecturas.updateOne(
  { "sensor.id": "TEST-001" },
  { $set: { "medicion.pm25": 99 } }
)

print("=== FIND con filtro ===")
printjson(db.lecturas.find({ "sensor.id": "TEST-001" }).toArray())

print("=== DELETE ONE ===")
db.lecturas.deleteOne({ "sensor.id": "TEST-001" })

print("=== Contar lecturas restantes ===")
print(db.lecturas.countDocuments())