// ------------------------------------------------------------
// INFORMACIÓN DINÁMICA NO ESTRUCTURADA (esquema flexible)
// Ejecutar DESPUÉS de 12_crear_eventos.py:
//   mongosh smartcity --file 13_info_dinamica.js
//
// Inserta en "eventos" documentos con estructuras DISTINTAS
// (campos, arreglos y subdocumentos diferentes) en la misma
// colección, sin alterar ningún esquema. En PostgreSQL esto
// exigiría ALTER TABLE, columnas NULL o tablas extra.
// ------------------------------------------------------------

print("=== 1. INSERTAR EVENTOS MANUALES CON ESTRUCTURAS DIFERENTES ===")
var zonaEj = db.lecturas.findOne({}).sensor.zona
var sensorEj = db.lecturas.findOne({}).sensor.id
print("Zona de ejemplo: " + zonaEj + " | Sensor de ejemplo: " + sensorEj)

db.eventos.insertMany([
  {
    origen: "manual",
    tipo: "obra_vial",
    zona: zonaEj,
    descripcion: "Reparación de calzada",
    detalles: { carriles_cerrados: 2, duracion_estimada_h: 6 },
    timestamp: new Date()
  },
  {
    origen: "manual",
    tipo: "evento_masivo",
    zona: zonaEj,
    detalles: {
      asistentes_estimados: 15000,
      vias_cerradas: ["Avenida 1", "Calle 5"],
      organizador: "Municipalidad"
    },
    etiquetas: ["concierto", "trafico"],
    timestamp: new Date()
  },
  {
    origen: "manual",
    tipo: "falla_sensor",
    sensor_id: sensorEj,
    zona: zonaEj,
    detalles: { ultimo_reporte: new Date(), bateria_pct: 12 },
    comentarios: [
      { autor: "tecnico1", texto: "Revisar alimentación", fecha: new Date() }
    ],
    timestamp: new Date()
  }
])
print("Insertados 3 eventos manuales con estructuras distintas")

print("\n=== 2. CONSULTAR POR CAMPOS QUE SOLO EXISTEN EN ALGUNOS DOCUMENTOS ===")
print("-- Eventos que tienen detalles.carriles_cerrados:")
printjson(db.eventos.find(
  { "detalles.carriles_cerrados": { $exists: true } },
  { _id: 0, tipo: 1, zona: 1, detalles: 1 }
).toArray())

print("-- Eventos con la etiqueta 'concierto' (búsqueda dentro de un arreglo):")
printjson(db.eventos.find(
  { etiquetas: "concierto" },
  { _id: 0, tipo: 1, etiquetas: 1, "detalles.asistentes_estimados": 1 }
).toArray())

print("-- Eventos con comentarios (arreglo de subdocumentos):")
printjson(db.eventos.find(
  { "comentarios.autor": "tecnico1" },
  { _id: 0, tipo: 1, sensor_id: 1, comentarios: 1 }
).toArray())

print("\n=== 3. AGREGAR UN CAMPO NUEVO SIN ALTERAR EL ESQUEMA ===")
db.eventos.updateOne(
  { origen: "manual", tipo: "obra_vial" },
  {
    $set: { "detalles.estado": "en_progreso" },
    $push: { comentarios: { autor: "inspector", texto: "Desvío habilitado", fecha: new Date() } }
  }
)
printjson(db.eventos.findOne({ origen: "manual", tipo: "obra_vial" }, { _id: 0 }))

print("\n=== 4. DIVERSIDAD DE ESTRUCTURAS EN LA MISMA COLECCIÓN ===")
printjson(db.eventos.aggregate([
  { $group: {
      _id: "$tipo",
      total: { $sum: 1 },
      campos_detalles: { $first: { $map: {
        input: { $objectToArray: { $ifNull: ["$detalles", {}] } },
        as: "c",
        in: "$$c.k"
      } } }
  }},
  { $sort: { total: -1 } }
]).toArray())

print("\n=== 5. LIMPIEZA (quita solo los eventos manuales de la demo) ===")
var del = db.eventos.deleteMany({ origen: "manual" })
print("Eventos manuales eliminados: " + del.deletedCount)
print("Eventos restantes: " + db.eventos.countDocuments({}))
print("\n=== FIN ===")