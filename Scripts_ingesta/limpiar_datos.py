import pandas as pd
import numpy as np

print("1. Cargando CSVs...")
df_trafico = pd.read_csv("smart_city_traffic_mobility.csv")
df_aire = pd.read_csv("datos_aire_cdmx.csv")

print(f"   Tráfico: {len(df_trafico)} filas")
print(f"   Aire: {len(df_aire)} filas")

# ============================================
# 2. LIMPIAR TRÁFICO
# ============================================
print("\n2. Limpiando tráfico...")

# Renombrar columnas clave
df_trafico = df_trafico.rename(columns={
    "city_zone": "zona",
    "intersection_id": "sensor_nombre",
    "vehicle_count": "carros",
    "timestamp": "fecha",
    "air_quality_index": "aqi"
})

# Convertir fecha
df_trafico["fecha"] = pd.to_datetime(df_trafico["fecha"], errors="coerce")

# Eliminar nulos y valores absurdos
df_trafico = df_trafico.dropna(subset=["fecha", "zona", "sensor_nombre"])
df_trafico = df_trafico[df_trafico["carros"] >= 0]

# Seleccionar y mapear columnas relevantes
df_trafico = df_trafico[[
    "sensor_nombre", "zona", "fecha",
    "carros", "aqi", "temperature", "congestion_score",
    "emission_estimate", "fuel_waste_estimate",
    "accident_reported", "is_weekend",
    "latitude", "longitude"
]].copy()

df_trafico = df_trafico.rename(columns={
    "temperature": "temperatura",
    "accident_reported": "accidente",
    "is_weekend": "es_fin_semana",
    "latitude": "latitud",
    "longitude": "longitud"
})

# Agregar columnas faltantes (pm25, pm10, no2, o3, co)
df_trafico["pm25"] = np.nan
df_trafico["pm10"] = np.nan
df_trafico["no2"] = np.nan
df_trafico["o3"] = np.nan
df_trafico["co"] = np.nan

print(f"   Tráfico limpio: {len(df_trafico)} filas")

# ============================================
# 3. LIMPIAR AIRE
# ============================================
print("\n3. Limpiando aire...")

# Convertir fecha
df_aire["fecha"] = pd.to_datetime(df_aire["fecha"], errors="coerce")
df_aire = df_aire.dropna(subset=["fecha"])

# Pivotear: cada fila tenía un solo parámetro (pm25, pm10, etc.)
# Queremos una fila por sensor+fecha con todas las columnas
df_aire_pivot = df_aire.pivot_table(
    index=["sensor_id", "zona", "fecha", "latitud", "longitud"],
    columns="parametro",
    values="valor",
    aggfunc="mean"
).reset_index()

df_aire_pivot.columns.name = None

# Renombrar
df_aire_pivot = df_aire_pivot.rename(columns={
    "sensor_id": "sensor_nombre",
})

# Agregar columnas faltantes
for col in ["carros", "aqi", "temperatura", "congestion_score",
            "emission_estimate", "fuel_waste_estimate"]:
    df_aire_pivot[col] = np.nan

df_aire_pivot["accidente"] = False
df_aire_pivot["es_fin_semana"] = df_aire_pivot["fecha"].dt.dayofweek >= 5

print(f"   Aire limpio: {len(df_aire_pivot)} filas")

# ============================================
# 4. UNIR LOS DOS
# ============================================
print("\n4. Uniendo los dos datasets...")

columnas_finales = [
    "sensor_nombre", "zona", "fecha",
    "pm25", "pm10", "no2", "o3", "co",
    "carros", "aqi", "temperatura", "congestion_score",
    "emission_estimate", "fuel_waste_estimate",
    "accidente", "es_fin_semana",
    "latitud", "longitud"
]

df_trafico = df_trafico[columnas_finales]
df_aire_pivot = df_aire_pivot[columnas_finales]

df_final = pd.concat([df_trafico, df_aire_pivot], ignore_index=True)

print(f"   Total unificado: {len(df_final)} filas")

# ============================================
# 5. GUARDAR
# ============================================
df_final.to_csv("datos_limpios.csv", index=False)
print(f"\n✅ Guardado: datos_limpios.csv con {len(df_final)} filas")
print(f"\nColumnas: {list(df_final.columns)}")
print(f"\nResumen:")
print(df_final.describe())