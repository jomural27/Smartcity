import pandas as pd

# --- CSV de tráfico ---
print("=" * 60)
print("CSV DE TRÁFICO")
print("=" * 60)
df_trafico = pd.read_csv("smart_city_traffic_mobility.csv")
print(f"Filas: {len(df_trafico)}")
print(f"Columnas: {len(df_trafico.columns)}")
print("\nNombres de columnas:")
for c in df_trafico.columns:
    print(f"  - {c}")
print("\nPrimeras 3 filas:")
print(df_trafico.head(3))
print("\nTipos de datos:")
print(df_trafico.dtypes)

# --- CSV de aire ---
print("\n" + "=" * 60)
print("CSV DE AIRE (CDMX)")
print("=" * 60)
df_aire = pd.read_csv("datos_aire_cdmx.csv")
print(f"Filas: {len(df_aire)}")
print(f"Columnas: {len(df_aire.columns)}")
print("\nNombres de columnas:")
for c in df_aire.columns:
    print(f"  - {c}")
print("\nPrimeras 3 filas:")
print(df_aire.head(3))
print("\nTipos de datos:")
print(df_aire.dtypes)