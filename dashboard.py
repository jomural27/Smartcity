import streamlit as st
import pandas as pd
import plotly.express as px
import psycopg2
from pymongo import MongoClient
from datetime import datetime

# ============================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================
st.set_page_config(
    page_title="SmartCity Analytics",
    page_icon="🚦",
    layout="wide"
)

st.title("🚦 SmartCity Analytics: Tráfico y Contaminación")
st.markdown("**Arquitectura de datos urbanos con PostgreSQL, MongoDB, HDFS y Apache Spark**")

# ============================================
# FUNCIONES DE CONEXIÓN
# ============================================
@st.cache_data(ttl=300)
def leer_postgres(query):
    conn = psycopg2.connect(
        host="localhost", port=5432,
        dbname="smartcity", user="admin", password="admin123"
    )
    df = pd.read_sql(query, conn)
    conn.close()
    return df

@st.cache_data(ttl=300)
def leer_mongo(coleccion="lecturas", limite=100000):
    client = MongoClient("mongodb://localhost:27017")
    data = list(client["smartcity"][coleccion].find({}, {"_id": 0}).limit(limite))
    return pd.DataFrame(data)

# ============================================
# SIDEBAR - FILTROS
# ============================================
st.sidebar.header("🔍 Filtros")

zonas_df = leer_postgres("SELECT DISTINCT nombre_zona FROM zona ORDER BY nombre_zona")
zonas = ["Todas"] + zonas_df["nombre_zona"].tolist()
zona_sel = st.sidebar.selectbox("Zona", zonas)

tipos = ["Todos", "trafico", "calidad_aire"]
tipo_sel = st.sidebar.selectbox("Tipo de sensor", tipos)

# ============================================
# CONSTRUIR FILTROS DINÁMICOS (antes del with)
# ============================================
where_zona = f" AND z.nombre_zona = '{zona_sel}'" if zona_sel != "Todas" else ""
where_tipo = f" AND s.tipo_sensor = '{tipo_sel}'" if tipo_sel != "Todos" else ""

# ============================================
# CARGA DE DATOS (con filtros)
# ============================================
with st.spinner("Cargando datos..."):

    try:
        kpi_data = leer_postgres(f"""
            SELECT 
                (SELECT COUNT(*) FROM medicion m
                 JOIN sensor s ON m.id_sensor = s.id_sensor
                 JOIN zona z ON s.id_zona = z.id_zona
                 WHERE 1=1 {where_zona} {where_tipo}) AS total_mediciones,
                (SELECT COUNT(*) FROM sensor s
                 JOIN zona z ON s.id_zona = z.id_zona
                 WHERE 1=1 {where_zona} {where_tipo}) AS total_sensores,
                (SELECT AVG(m.pm25) FROM medicion m
                 JOIN sensor s ON m.id_sensor = s.id_sensor
                 JOIN zona z ON s.id_zona = z.id_zona
                 WHERE m.pm25 IS NOT NULL {where_zona} {where_tipo}) AS pm25_prom,
                (SELECT AVG(m.carros) FROM medicion m
                 JOIN sensor s ON m.id_sensor = s.id_sensor
                 JOIN zona z ON s.id_zona = z.id_zona
                 WHERE m.carros IS NOT NULL {where_zona} {where_tipo}) AS carros_prom,
                (SELECT AVG(m.congestion_score) FROM medicion m
                 JOIN sensor s ON m.id_sensor = s.id_sensor
                 JOIN zona z ON s.id_zona = z.id_zona
                 WHERE m.congestion_score IS NOT NULL {where_zona} {where_tipo}) AS congestion_prom
        """)
        total_mediciones = int(kpi_data["total_mediciones"][0] or 0)
        total_sensores = int(kpi_data["total_sensores"][0] or 0)
        pm25_prom = float(kpi_data["pm25_prom"][0] or 0)
        carros_prom = float(kpi_data["carros_prom"][0] or 0)
        congestion_prom = float(kpi_data["congestion_prom"][0] or 0)
    except Exception as e:
        st.error(f"Error cargando KPIs: {e}")
        total_mediciones = total_sensores = 0
        pm25_prom = carros_prom = congestion_prom = 0

    try:
        client = MongoClient("mongodb://localhost:27017")
        total_alertas = client["smartcity"]["alertas"].count_documents({})
    except:
        total_alertas = 0

# ============================================
# KPIs (fila superior)
# ============================================
st.markdown("### 📊 Indicadores Clave (KPIs)")
col1, col2, col3, col4, col5, col6 = st.columns(6)

col1.metric("🌫️ PM2.5 promedio", f"{pm25_prom:.2f}")
col2.metric("🚗 Vehículos prom.", f"{carros_prom:.0f}")
col3.metric("🚦 Congestión prom.", f"{congestion_prom:.1f}")
col4.metric("📡 Sensores", f"{total_sensores:,}")
col5.metric("📈 Mediciones", f"{total_mediciones:,}")
col6.metric("⚠️ Alertas", f"{total_alertas:,}")

st.markdown("---")


# ============================================
# GRÁFICO 1: SERIE TEMPORAL (MongoDB)
# ============================================
st.subheader("📈 Evolución temporal de PM2.5")
try:
    client = MongoClient("mongodb://localhost:27017")
    pipeline = [
        {"$match": {"medicion.pm25": {"$ne": None}}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m", "date": "$timestamp"}},
            "pm25_prom": {"$avg": "$medicion.pm25"},
            "total": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]
    resultado = list(client["smartcity"]["lecturas"].aggregate(pipeline))
    
    if resultado:
        df_serie = pd.DataFrame(resultado).rename(columns={"_id": "mes"})
        fig1 = px.line(df_serie, x="mes", y="pm25_prom", markers=True,
                       title="Promedio mensual de PM2.5 (MongoDB)")
        fig1.update_traces(line=dict(width=3))
        st.plotly_chart(fig1, width="stretch")
        st.caption(f"📌 **Fuente:** MongoDB (Aggregation sobre {len(df_serie)} meses)")
    else:
        st.warning("La aggregation devolvió 0 filas. Verifica que Mongo tenga datos con pm25.")
except Exception as e:
    st.error(f"Error en gráfico 1: {e}")

# ============================================
# GRÁFICO 2: COMPARATIVA POR ZONAS (con filtros)
# ============================================
st.subheader("🏙️ Comparativa por zonas")
try:
    df_zonas = leer_postgres(f"""
        SELECT z.nombre_zona, 
               AVG(m.pm25) AS pm25_prom,
               AVG(m.carros) AS carros_prom,
               COUNT(*) AS total
        FROM medicion m
        JOIN sensor s ON m.id_sensor = s.id_sensor
        JOIN zona z ON s.id_zona = z.id_zona
        WHERE m.pm25 IS NOT NULL {where_zona} {where_tipo}
        GROUP BY z.nombre_zona
        ORDER BY pm25_prom DESC
        LIMIT 15
    """)
    if not df_zonas.empty:
        fig2 = px.bar(df_zonas, x="nombre_zona", y="pm25_prom",
                      color="pm25_prom", color_continuous_scale="Reds",
                      title="PM2.5 promedio por zona")
        fig2.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig2, width="stretch")
        st.caption(f"📌 **Fuente:** PostgreSQL (filtros: zona={zona_sel}, tipo={tipo_sel})")
    else:
        st.info("No hay datos para los filtros seleccionados")
except Exception as e:
    st.warning(f"Error en gráfico 2: {e}")

# ============================================
# GRÁFICO 3: DISTRIBUCIÓN DE SENSORES POR TIPO
# ============================================
st.subheader("📊 Distribución de sensores por tipo")
try:
    df_tipos = leer_postgres(f"""
        SELECT s.tipo_sensor, COUNT(*) AS total
        FROM sensor s
        JOIN zona z ON s.id_zona = z.id_zona
        WHERE 1=1 {where_zona} {where_tipo}
        GROUP BY s.tipo_sensor
        ORDER BY total DESC
    """)
    if not df_tipos.empty:
        fig3 = px.pie(df_tipos, names="tipo_sensor", values="total",
                      title="Tipos de sensores en la red",
                      hole=0.4)
        st.plotly_chart(fig3, width="stretch")
        st.caption(f"📌 **Fuente:** PostgreSQL (filtros: zona={zona_sel})")
    else:
        st.info("No hay sensores con los filtros seleccionados")
except Exception as e:
    st.warning(f"Error en gráfico 3: {e}")

# ============================================
# GRÁFICO 4: RESULTADO DE SPARK
# ============================================
st.subheader("⚡ Resultado de Apache Spark")
try:
    # Solo zonas que SÍ tienen pm25 (vienen de OpenAQ)
    df_spark = leer_postgres("""
        SELECT zona, pm25_prom, congestion_prom, total_lecturas
        FROM resultado_spark_zonas 
        WHERE pm25_prom IS NOT NULL
        ORDER BY pm25_prom DESC 
        LIMIT 15
    """)
    
    # Si no hay zonas con pm25, mostrar tráfico en su lugar
    if df_spark.empty:
        st.info("No hay zonas con PM2.5 registrado. Mostrando top zonas por tráfico:")
        df_spark = leer_postgres("""
            SELECT zona, carros_prom, congestion_prom, total_lecturas,
                   carros_prom AS pm25_prom
            FROM resultado_spark_zonas 
            WHERE carros_prom IS NOT NULL
            ORDER BY carros_prom DESC 
            LIMIT 15
        """)
        metrica = "Vehículos promedio"
        color_scale = "Blues"
    else:
        metrica = "PM2.5 promedio"
        color_scale = "Oranges"
    
    if not df_spark.empty:
        fig4 = px.bar(
            df_spark,
            x="pm25_prom",
            y="zona",
            orientation="h",
            color="pm25_prom",
            color_continuous_scale=color_scale,
            title=f"Ranking de zonas por {metrica} (Apache Spark)"
        )
        fig4.update_layout(
            yaxis={"categoryorder": "total ascending"},
            height=500
        )
        st.plotly_chart(fig4, width="stretch")
        st.caption("📌 **Fuente:** Apache Spark SQL (PostgreSQL: `resultado_spark_zonas`)")
    else:
        st.warning("La tabla resultado_spark_zonas no tiene datos")
except Exception as e:
    st.warning(f"Error en gráfico 4: {e}")

# ============================================
# TABLA DE DETALLE (con filtros)
# ============================================
st.markdown("---")
st.subheader("📋 Muestra de datos de mediciones")
try:
    df_tabla = leer_postgres(f"""
        SELECT m.id_medicion, s.nombre AS sensor, z.nombre_zona AS zona,
               m.pm25, m.carros, m.temperatura, m.fecha
        FROM medicion m
        JOIN sensor s ON m.id_sensor = s.id_sensor
        JOIN zona z ON s.id_zona = z.id_zona
        WHERE 1=1 {where_zona} {where_tipo}
        LIMIT 100
    """)
    st.dataframe(df_tabla, width="stretch")
    st.caption(f"📌 **Fuente:** PostgreSQL (filtros: zona={zona_sel}, tipo={tipo_sel})")
except Exception as e:
    st.warning(f"Error en tabla: {e}")

# ============================================
# SELECTOR DE TECNOLOGÍA
# ============================================
st.markdown("---")
st.subheader("🔧 Explorador de consultas por tecnología")

tecnologia = st.selectbox(
    "Selecciona la tecnología:",
    ["PostgreSQL", "MongoDB", "Spark (vía PostgreSQL)"]
)

if tecnologia == "PostgreSQL":
    st.code("""
-- Top 10 sensores con más mediciones
SELECT s.nombre, COUNT(*) AS total
FROM medicion m
JOIN sensor s ON m.id_sensor = s.id_sensor
GROUP BY s.nombre
ORDER BY total DESC
LIMIT 10;
    """, language="sql")
    try:
        df_pg = leer_postgres("""
            SELECT s.nombre, COUNT(*) AS total
            FROM medicion m
            JOIN sensor s ON m.id_sensor = s.id_sensor
            GROUP BY s.nombre
            ORDER BY total DESC
            LIMIT 10
        """)
        st.dataframe(df_pg, use_container_width=True)
        st.caption("📌 **Fuente:** PostgreSQL")
    except Exception as e:
        st.warning(f"Error: {e}")

elif tecnologia == "MongoDB":
    st.code("""
// Top 10 zonas por contaminación promedio
db.lecturas.aggregate([
  { $match: { "medicion.pm25": { $ne: null } } },
  { $group: {
      _id: "$sensor.zona",
      promedio: { $avg: "$medicion.pm25" }
  }},
  { $sort: { promedio: -1 } },
  { $limit: 10 }
])
    """, language="javascript")
    try:
        client = MongoClient("mongodb://localhost:27017")
        pipeline = [
            {"$match": {"medicion.pm25": {"$ne": None}}},
            {"$group": {"_id": "$sensor.zona", "promedio": {"$avg": "$medicion.pm25"}}},
            {"$sort": {"promedio": -1}},
            {"$limit": 10}
        ]
        resultado = list(client["smartcity"]["lecturas"].aggregate(pipeline))
        df_mongo = pd.DataFrame(resultado).rename(columns={"_id": "zona", "promedio": "pm25_prom"})
        st.dataframe(df_mongo, use_container_width=True)
        st.caption("📌 **Fuente:** MongoDB (Aggregation Framework)")
    except Exception as e:
        st.warning(f"Error: {e}")

else:  # Spark
    st.code("""
# Spark SQL
resultado = df.groupBy("zona") \\
    .agg(avg("pm25").alias("pm25_prom"),
         count("*").alias("total"))
    .orderBy(desc("pm25_prom"))
    """, language="python")
    try:
        df_spark2 = leer_postgres("""
            SELECT zona, pm25_prom, total_lecturas
            FROM resultado_spark_zonas
            ORDER BY pm25_prom DESC
        """)
        st.dataframe(df_spark2, use_container_width=True)
        st.caption("📌 **Fuente:** Apache Spark (resultado guardado en PostgreSQL)")
    except Exception as e:
        st.warning(f"Error: {e}")

# ============================================
# PIE DE PÁGINA
# ============================================
st.markdown("---")
st.markdown("""
**SmartCity Analytics** | Proyecto CE3101 - Semestre II 2026  
Arquitectura: PostgreSQL + MongoDB + HDFS + Apache Spark  
Dashboard construido con Streamlit
""")