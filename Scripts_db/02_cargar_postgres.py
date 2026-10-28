import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

# ============================================
# 1. CONECTAR
# ============================================
print("Conectando a PostgreSQL...")
conn = psycopg2.connect(
    host="localhost", port=5432,
    dbname="smartcity", user="admin", password="admin123"
)
cur = conn.cursor()

# ============================================
# 2. LIMPIAR TABLAS (por si acaso)
# ============================================
print("Limpiando tablas...")
cur.execute("TRUNCATE medicion, organismo, sensor, categoria_sensor, zona, ciudad RESTART IDENTITY CASCADE;")

# ============================================
# 3. CIUDAD
# ============================================
print("Insertando ciudad...")
cur.execute("INSERT INTO ciudad (nombre) VALUES ('Smart City') RETURNING id_ciudad;")
id_ciudad = cur.fetchone()[0]

# ============================================
# 4. LEER CSV
# ============================================
print("Leyendo datos_limpios.csv...")
df = pd.read_csv("datos_limpios.csv")

# CORRECCIÓN: la columna fecha tiene formatos mixtos (con y sin +00:00)
# - format="mixed": infiere el formato fila por fila
# - utc=True: unifica todo a UTC
# - tz_localize(None): quita la zona horaria (para columna TIMESTAMP)
#   Si tu columna es TIMESTAMPTZ, quita el .dt.tz_localize(None)
df["fecha"] = pd.to_datetime(df["fecha"], format="mixed", utc=True).dt.tz_localize(None)
print(f"   Filas: {len(df)}")

# ============================================
# 5. ZONAS
# ============================================
print("Insertando zonas...")
zonas = df[["zona", "latitud", "longitud"]].drop_duplicates(subset=["zona"]).dropna(subset=["zona"])
zona_map = {}
for _, row in zonas.iterrows():
    cur.execute("""
        INSERT INTO zona (nombre_zona, ciudad_origen, latitud, longitud, id_ciudad)
        VALUES (%s, %s, %s, %s, %s) RETURNING id_zona;
    """, (row["zona"], "Mixto", float(row["latitud"]), float(row["longitud"]), id_ciudad))
    zona_map[row["zona"]] = cur.fetchone()[0]
print(f"   {len(zona_map)} zonas insertadas")

# ============================================
# 6. CATEGORÍAS
# ============================================
print("Insertando categorías...")
categorias = ["movilidad", "ambiente", "energia", "iot", "clima"]
cat_map = {}
for c in categorias:
    cur.execute("INSERT INTO categoria_sensor (nombre_categoria) VALUES (%s) RETURNING id_categoria;", (c,))
    cat_map[c] = cur.fetchone()[0]
print(f"   {len(cat_map)} categorías insertadas")

# ============================================
# 7. SENSORES
# ============================================
print("Insertando sensores...")
sensores = df[["sensor_nombre", "zona"]].drop_duplicates(subset=["sensor_nombre"]).dropna()
sensor_map = {}

for _, row in sensores.iterrows():
    # Asignar categoría según el nombre del sensor
    nombre = str(row["sensor_nombre"])
    if "CDMX" in nombre:
        cat = "ambiente"
        tipo = "calidad_aire"
    else:
        cat = "movilidad"
        tipo = "trafico"

    cur.execute("""
        INSERT INTO sensor (nombre, tipo_sensor, estado, id_zona, id_categoria)
        VALUES (%s, %s, 'activo', %s, %s) RETURNING id_sensor;
    """, (nombre, tipo, zona_map[row["zona"]], cat_map[cat]))
    sensor_map[nombre] = cur.fetchone()[0]
print(f"   {len(sensor_map)} sensores insertados")

# ============================================
# 8. ORGANISMOS
# ============================================
print("Insertando organismos...")
organismos = [
    ("MOPT", "Ministro de Obras Públicas"),
    ("MINAE", "Ministro de Ambiente y Energía"),
    ("Municipalidad", "Alcalde Municipal"),
    ("CNFL", "Gerente de Energía"),
]
# Asignar cada organismo a un sensor distinto
sensor_ids = list(sensor_map.values())[:4]
for (nombre, resp), sid in zip(organismos, sensor_ids):
    cur.execute("INSERT INTO organismo (nombre, responsable, id_sensor) VALUES (%s, %s, %s);",
                (nombre, resp, sid))
print(f"   {len(organismos)} organismos insertados")

# ============================================
# 9. MEDICIONES (1M filas)
# ============================================
print("Insertando mediciones (esto puede tardar 1-3 minutos)...")

columnas = [
    "id_sensor", "pm25", "pm10", "no2", "o3", "co",
    "carros", "temperatura", "aqi", "congestion_score",
    "emission_estimate", "fuel_waste_estimate",
    "accidente", "es_fin_semana", "fecha"
]

# Preparar datos
df["id_sensor"] = df["sensor_nombre"].map(sensor_map)
# CORRECCIÓN: .copy() evita el SettingWithCopyWarning
df_med = df.dropna(subset=["id_sensor"]).copy()
df_med["id_sensor"] = df_med["id_sensor"].astype(int)

# CORRECCIÓN: convertir a object primero para que NaN/NaT pasen a None de verdad
df_med = df_med[columnas].astype(object)
df_med = df_med.where(pd.notna(df_med), None)

# CORRECCIÓN: accidente y es_fin_semana son BOOLEAN en Postgres, pero en el CSV son 0/1
for col in ["accidente", "es_fin_semana"]:
    df_med[col] = df_med[col].map(lambda v: None if v is None else bool(int(v)))

registros = df_med.values.tolist()

# Insertar por lotes (más rápido que uno por uno)
BATCH_SIZE = 10000
total = len(registros)

for i in range(0, total, BATCH_SIZE):
    lote = registros[i:i + BATCH_SIZE]
    execute_values(
        cur,
        """INSERT INTO medicion
        (id_sensor, pm25, pm10, no2, o3, co, carros, temperatura, aqi,
         congestion_score, emission_estimate, fuel_waste_estimate,
         accidente, es_fin_semana, fecha)
        VALUES %s""",
        lote
    )
    print(f"   Insertados: {min(i + BATCH_SIZE, total)}/{total}")

conn.commit()

# ============================================
# 10. ACTUALIZAR VISTA
# ============================================
print("Refrescando vista materializada...")
cur.execute("REFRESH MATERIALIZED VIEW resumen_zonas;")
conn.commit()

# ============================================
# 11. VERIFICAR
# ============================================
cur.execute("SELECT COUNT(*) FROM medicion;")
print(f"\n✅ Total mediciones: {cur.fetchone()[0]}")

cur.execute("SELECT COUNT(*) FROM sensor;")
print(f"✅ Total sensores: {cur.fetchone()[0]}")

cur.execute("SELECT COUNT(*) FROM zona;")
print(f"✅ Total zonas: {cur.fetchone()[0]}")

cur.close()
conn.close()
print("\n¡Carga completa!")