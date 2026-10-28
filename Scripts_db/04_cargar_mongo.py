
# Carga 500k docs en la colección lecturas + genera alertas


import pandas as pd
from pymongo import MongoClient

# --- Funciones auxiliares ---
def safe_float(v):
    return float(v) if pd.notna(v) else None

def safe_int(v):
    return int(v) if pd.notna(v) else None

def safe_bool(v):
    return bool(v) if pd.notna(v) else False

# --- Conectar ---
print("Conectando a MongoDB...")
client = MongoClient("mongodb://localhost:27017")
db = client["smartcity"]

# --- Limpiar ---
print("Limpiando colecciones...")
db["lecturas"].drop()
db["alertas"].drop()

# --- Leer CSV ---
print("Leyendo datos_limpios.csv...")
df = pd.read_csv("datos_limpios.csv")
df["fecha"] = pd.to_datetime(df["fecha"], format="mixed", utc=True)
print(f"   Total filas: {len(df)}")

# Tomar 500,000 filas
df = df.sample(n=min(500000, len(df)), random_state=42).sort_values("fecha")
print(f"   Usando {len(df)} filas")

# --- Preparar documentos ---
print("Preparando documentos...")
documentos = []
for _, row in df.iterrows():
    doc = {
        "sensor": {
            "id": str(row["sensor_nombre"]),
            "zona": str(row["zona"]),
            "ubicacion": {
                "lat": safe_float(row["latitud"]),
                "lon": safe_float(row["longitud"])
            }
        },
        "medicion": {
            "pm25": safe_float(row["pm25"]),
            "pm10": safe_float(row["pm10"]),
            "no2": safe_float(row["no2"]),
            "o3": safe_float(row["o3"]),
            "co": safe_float(row["co"]),
            "carros": safe_int(row["carros"]),
            "temperatura": safe_float(row["temperatura"]),
            "aqi": safe_int(row["aqi"]),
            "congestion_score": safe_float(row["congestion_score"]),
            "emission_estimate": safe_float(row["emission_estimate"]),
            "fuel_waste_estimate": safe_float(row["fuel_waste_estimate"])
        },
        "eventos": {
            "accidente": safe_bool(row["accidente"]),
            "es_fin_semana": safe_bool(row["es_fin_semana"])
        },
        "timestamp": row["fecha"].to_pydatetime()
    }
    documentos.append(doc)

# --- Insertar en lotes ---
print(f"Insertando {len(documentos)} documentos...")
BATCH_SIZE = 10000
total = len(documentos)
for i in range(0, total, BATCH_SIZE):
    lote = documentos[i:i + BATCH_SIZE]
    db["lecturas"].insert_many(lote)
    print(f"   Insertados: {min(i + BATCH_SIZE, total)}/{total}")

print(f"✅ Total en 'lecturas': {db['lecturas'].count_documents({})}")

# --- Generar alertas ---
print("\nGenerando alertas...")
umbral_pm25 = 50
umbral_congestion = 70

alertas = []
for doc in documentos:
    pm25 = doc["medicion"]["pm25"]
    congestion = doc["medicion"]["congestion_score"]

    if pm25 is not None and pm25 > umbral_pm25:
        alertas.append({
            "sensor_id": doc["sensor"]["id"],
            "zona": doc["sensor"]["zona"],
            "tipo_alerta": "contaminacion_alta",
            "valor": pm25,
            "umbral": umbral_pm25,
            "nivel": "critico" if pm25 > 100 else "moderado",
            "timestamp": doc["timestamp"]
        })

    if congestion is not None and congestion > umbral_congestion:
        alertas.append({
            "sensor_id": doc["sensor"]["id"],
            "zona": doc["sensor"]["zona"],
            "tipo_alerta": "congestion_alta",
            "valor": congestion,
            "umbral": umbral_congestion,
            "nivel": "critico" if congestion > 90 else "moderado",
            "timestamp": doc["timestamp"]
        })

if alertas:
    print(f"Insertando {len(alertas)} alertas...")
    for i in range(0, len(alertas), BATCH_SIZE):
        lote = alertas[i:i + BATCH_SIZE]
        db["alertas"].insert_many(lote)
    print(f"✅ Total en 'alertas': {db['alertas'].count_documents({})}")
else:
    print("No se generaron alertas")

client.close()
print("\n¡Carga completa!")