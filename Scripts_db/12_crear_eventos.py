from pymongo import MongoClient

# ------------------------------------------------------------
# Crea la colección "eventos" a partir de las lecturas ya
# cargadas en Mongo. Un evento es una lectura que cumple una
# condición crítica:
#   - contaminacion_critica : PM2.5 > 100
#   - congestion_severa     : congestion_score > 90
#   - accidente             : eventos.accidente == True
#
# El subdocumento "detalles" es DINÁMICO: cada tipo de evento
# guarda solo los campos que le aplican (y se omiten los nulos),
# por eso no todos los documentos tienen la misma estructura.
# ------------------------------------------------------------

BATCH_SIZE = 10000
UMBRAL_PM25_CRITICO = 100
UMBRAL_CONGESTION_SEVERA = 90


def limpiar(d):
    """Quita las claves con valor None (esquema flexible)."""
    return {k: v for k, v in d.items() if v is not None}


print("Conectando a MongoDB...")
client = MongoClient("mongodb://localhost:27017")
db = client["smartcity"]

print("Limpiando colección 'eventos'...")
db["eventos"].drop()

filtro = {
    "$or": [
        {"medicion.pm25": {"$gt": UMBRAL_PM25_CRITICO}},
        {"medicion.congestion_score": {"$gt": UMBRAL_CONGESTION_SEVERA}},
        {"eventos.accidente": True},
    ]
}
proyeccion = {"sensor": 1, "medicion": 1, "eventos": 1, "timestamp": 1}

print("Buscando lecturas críticas en 'lecturas'...")
cursor = db["lecturas"].find(filtro, proyeccion).batch_size(BATCH_SIZE)

lote = []
total = 0
por_tipo = {}


def guardar(evento):
    global total
    lote.append(evento)
    por_tipo[evento["tipo"]] = por_tipo.get(evento["tipo"], 0) + 1
    if len(lote) >= BATCH_SIZE:
        db["eventos"].insert_many(lote)
        total += len(lote)
        lote.clear()
        print(f"   Insertados: {total}")


for lec in cursor:
    s = lec.get("sensor", {})
    m = lec.get("medicion", {})
    ev = lec.get("eventos", {})

    base = {
        "lectura_id": lec["_id"],
        "sensor_id": s.get("id"),
        "zona": s.get("zona"),
        "ubicacion": s.get("ubicacion"),
        "origen": "automatico",
        "timestamp": lec["timestamp"],
    }

    pm25 = m.get("pm25")
    if pm25 is not None and pm25 > UMBRAL_PM25_CRITICO:
        e = dict(base)
        e["tipo"] = "contaminacion_critica"
        e["severidad"] = "critica" if pm25 > 150 else "alta"
        e["detalles"] = limpiar({
            "pm25": pm25,
            "pm10": m.get("pm10"),
            "no2": m.get("no2"),
            "o3": m.get("o3"),
            "co": m.get("co"),
            "umbral_pm25": UMBRAL_PM25_CRITICO,
        })
        guardar(e)

    cong = m.get("congestion_score")
    if cong is not None and cong > UMBRAL_CONGESTION_SEVERA:
        e = dict(base)
        e["tipo"] = "congestion_severa"
        e["severidad"] = "critica" if cong > 95 else "alta"
        e["detalles"] = limpiar({
            "congestion_score": cong,
            "carros": m.get("carros"),
            "emission_estimate": m.get("emission_estimate"),
            "fuel_waste_estimate": m.get("fuel_waste_estimate"),
            "umbral_congestion": UMBRAL_CONGESTION_SEVERA,
        })
        guardar(e)

    if ev.get("accidente") is True:
        e = dict(base)
        e["tipo"] = "accidente"
        e["severidad"] = "alta"
        e["detalles"] = limpiar({
            "carros": m.get("carros"),
            "congestion_score": m.get("congestion_score"),
            "temperatura": m.get("temperatura"),
            "es_fin_semana": ev.get("es_fin_semana"),
        })
        guardar(e)

# Insertar lo que quedó pendiente
if lote:
    db["eventos"].insert_many(lote)
    total += len(lote)
    lote.clear()

print(f"✅ Total en 'eventos': {db['eventos'].count_documents({})}")
for tipo, n in por_tipo.items():
    print(f"   {tipo}: {n}")

print("Creando índices en 'eventos'...")
db["eventos"].create_index([("tipo", 1)])
db["eventos"].create_index([("zona", 1)])
db["eventos"].create_index([("sensor_id", 1)])
db["eventos"].create_index([("severidad", 1)])
db["eventos"].create_index([("timestamp", -1)])
db["eventos"].create_index([("zona", 1), ("tipo", 1)])
print("✅ Índices creados")

client.close()
print("\n¡Listo!")