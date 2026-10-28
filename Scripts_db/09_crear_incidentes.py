from pymongo import MongoClient
import pandas as pd
import random

print("Conectando a MongoDB...")
client = MongoClient("mongodb://localhost:27017")
db = client["smartcity"]

# Limpiar si existe
db["incidentes"].drop()
print("Colección 'incidentes' limpiada")

# Leer CSV
print("Leyendo datos_limpios.csv...")
df = pd.read_csv("datos_limpios.csv")

# Filtrar solo accidentes
df_acc = df[df["accidente"] == 1].copy()
print(f"Total de accidentes en el CSV: {len(df_acc)}")

# Tomar muestra si hay demasiados
if len(df_acc) > 5000:
    df_acc = df_acc.sample(n=5000, random_state=42)
print(f"Insertando {len(df_acc)} incidentes...")

# Tipos y gravedades
tipos_incidente = ["accidente_vehicular", "colision_multiple", "atropello", "derrape", "falla_mecanica"]
gravedades = ["baja", "media", "alta", "critica"]

# Preparar documentos
incidentes = []
for _, row in df_acc.iterrows():
    incidente = {
        "sensor_id": str(row["sensor_nombre"]),
        "zona": str(row["zona"]),
        "tipo": random.choice(tipos_incidente),
        "gravedad": random.choice(gravedades),
        "ubicacion": {
            "lat": float(row["latitud"]) if pd.notna(row["latitud"]) else None,
            "lon": float(row["longitud"]) if pd.notna(row["longitud"]) else None
        },
        "vehiculos_involucrados": random.randint(1, 5),
        "tiempo_respuesta_min": random.randint(5, 60),
        "timestamp": pd.to_datetime(row["fecha"], format="mixed", utc=True).to_pydatetime()
    }
    incidentes.append(incidente)

# Insertar por lotes
if incidentes:
    for i in range(0, len(incidentes), 1000):
        lote = incidentes[i:i+1000]
        db["incidentes"].insert_many(lote)
    print(f"✅ Total en 'incidentes': {db['incidentes'].count_documents({})}")
else:
    print("⚠️ No se generaron incidentes")

client.close()
print("\n¡Listo!")