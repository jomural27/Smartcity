from openaq import OpenAQ
import pandas as pd

# --- CONFIGURACIÓN ---
API_KEY = "d85d029383d57880358316ba008ac7841491c74190d36949eae1ea0b9d150f04"
CDMX_LAT = 19.4326
CDMX_LON = -99.1332
RADIO_METROS = 25000

# --- CONECTAR ---
client = OpenAQ(api_key=API_KEY)

print("Buscando estaciones cerca de CDMX...")
locations = client.locations.list(
    coordinates=(CDMX_LAT, CDMX_LON),
    radius=RADIO_METROS,
    limit=100
)

print(f"Total estaciones encontradas: {len(locations.results)}")

todas_mediciones = []
estaciones_procesadas = 0

# --- RECORRER TODAS LAS ESTACIONES ---
for loc in locations.results:
    estaciones_procesadas += 1
    print(f"\n[{estaciones_procesadas}/{len(locations.results)}] 📍 {loc.name} (ID: {loc.id})")

    try:
        sensores = client.locations.sensors(loc.id)
    except Exception as e:
        print(f"   Error obteniendo sensores: {e}")
        continue

    for sensor in sensores.results:
        parametro = sensor.parameter.name.lower()

        # Solo contaminantes relevantes
        if parametro not in ["pm25", "pm10", "no2", "o3", "co"]:
            continue

        print(f"   → {parametro.upper()} (sensor ID: {sensor.id})")

        # Paginar hasta 5 páginas (5000 registros por sensor)
        for page in range(1, 6):
            try:
                mediciones = client.measurements.list(
                    sensors_id=sensor.id,
                    data="hours",
                    limit=1000,
                    page=page
                )

                if not mediciones.results:
                    break

                print(f"      Página {page}: {len(mediciones.results)} registros")

                for m in mediciones.results:
                    todas_mediciones.append({
                        "sensor_id": f"CDMX_{loc.id}_{sensor.id}",
                        "zona": loc.name,
                        "parametro": parametro,
                        "pm25": m.value if parametro == "pm25" else None,
                        "valor": m.value,
                        "fecha": m.period.datetime_to.utc,
                        "latitud": loc.coordinates.latitude,
                        "longitud": loc.coordinates.longitude
                    })
            except Exception as e:
                print(f"      Error página {page}: {e}")
                break

# --- GUARDAR ---
if todas_mediciones:
    df = pd.DataFrame(todas_mediciones)
    df.to_csv("datos_aire_cdmx.csv", index=False)
    print(f"\n✅ Guardado: {len(df)} registros en datos_aire_cdmx.csv")
    print(f"\nDistribución por parámetro:")
    print(df["parametro"].value_counts())
    print(f"\nPrimeras 5 filas:")
    print(df.head())
else:
    print("\n⚠️ No se obtuvieron mediciones")

client.close()