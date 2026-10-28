# SmartCity Analytics

Proyecto de Bases de Datos (CE3101). Arquitectura de datos urbanos con PostgreSQL, MongoDB, Apache Hadoop y Apache Spark.

## 🚀 Cómo ejecutar el proyecto

### Requisitos
- Docker Desktop (con WSL 2 en Windows).
- Python 3.10+
- Librerías de Python: `pip install pandas psycopg2-binary pymongo streamlit plotly`

### Pasos
1. Levantar la infraestructura:
   `docker compose up -d`
   *(Esperar 1 minuto a que todos los contenedores digan "Up").*

2. Cargar los datos:
   `python scripts_db/02_cargar_postgres.py`
   `python scripts_db/04_cargar_mongo.py`

3. Subir datos a HDFS:
   `docker cp datos_limpios.csv namenode:/tmp/`
   `docker exec namenode hdfs dfs -mkdir -p /historico`
   `docker exec namenode hdfs dfs -put -f /tmp/datos_limpios.csv /historico/`

4. Abrir los notebooks de Spark (Jupyter):
   - `docker logs jupyter` (para obtener el token)
   - Abrir `http://localhost:8888`

5. Correr el Dashboard:
   `python dashboard/dashboard.py`