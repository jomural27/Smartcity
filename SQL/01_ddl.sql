-- ============================================================
-- 01_ddl.sql  |  SmartCity Analytics  |  PostgreSQL 16
-- ESQUEMA FINAL. Pensado para una base VACIA (no contiene DROP).
-- NO lo ejecutes sobre tu base actual (ya tiene estas tablas):
-- tu base actual llega a este mismo estado con 03_migraciones.sql.
-- Una vez que todo funcione, compara con:
--   docker exec postgres pg_dump -U admin -d smartcity --schema-only --no-owner
-- ============================================================

-- 1. CIUDAD
CREATE TABLE ciudad (
    id_ciudad SERIAL PRIMARY KEY,
    nombre    VARCHAR(100) NOT NULL UNIQUE
);

-- 2. ZONA (entidad "Ubicaciones" del enunciado)
CREATE TABLE zona (
    id_zona       SERIAL PRIMARY KEY,
    nombre_zona   VARCHAR(100) NOT NULL,
    ciudad_origen VARCHAR(50),
    distrito      VARCHAR(100),
    latitud       DOUBLE PRECISION,
    longitud      DOUBLE PRECISION,
    id_ciudad     INTEGER NOT NULL REFERENCES ciudad(id_ciudad)
);

-- 3. CATEGORIA DE SENSOR
CREATE TABLE categoria_sensor (
    id_categoria     SERIAL PRIMARY KEY,
    nombre_categoria VARCHAR(50) NOT NULL UNIQUE
);

-- 4. ORGANISMO RESPONSABLE (3FN: un organismo NO depende de un sensor)
CREATE TABLE organismo (
    id_organismo SERIAL PRIMARY KEY,
    nombre       VARCHAR(100) NOT NULL UNIQUE,
    responsable  VARCHAR(100)
);

-- 5. SENSOR (la FK a organismo vive aqui: un organismo tiene muchos sensores)
CREATE TABLE sensor (
    id_sensor         SERIAL PRIMARY KEY,
    nombre            VARCHAR(100) NOT NULL UNIQUE,
    tipo_sensor       VARCHAR(50),
    estado            VARCHAR(20) DEFAULT 'activo',
    fecha_instalacion DATE,
    id_zona           INTEGER NOT NULL REFERENCES zona(id_zona),
    id_categoria      INTEGER NOT NULL REFERENCES categoria_sensor(id_categoria),
    id_organismo      INTEGER NOT NULL REFERENCES organismo(id_organismo)
);

-- 6. USUARIOS DEL SISTEMA
CREATE TABLE usuarios (
    id_usuario SERIAL PRIMARY KEY,
    nombre     VARCHAR(100) NOT NULL,
    correo     VARCHAR(150) NOT NULL UNIQUE
);

-- 7. MEDICION, particionada por rango de fecha.
--    La PK debe incluir la columna de particion (fecha).
CREATE TABLE medicion (
    id_medicion         SERIAL,
    id_sensor           INTEGER NOT NULL,
    pm25                DOUBLE PRECISION,
    pm10                DOUBLE PRECISION,
    no2                 DOUBLE PRECISION,
    o3                  DOUBLE PRECISION,
    co                  DOUBLE PRECISION,
    carros              INTEGER,
    temperatura         DOUBLE PRECISION,
    aqi                 INTEGER,
    congestion_score    DOUBLE PRECISION,
    emission_estimate   DOUBLE PRECISION,
    fuel_waste_estimate DOUBLE PRECISION,
    accidente           BOOLEAN DEFAULT FALSE,
    es_fin_semana       BOOLEAN DEFAULT FALSE,
    fecha               TIMESTAMP NOT NULL,
    CONSTRAINT fk_medicion_sensor FOREIGN KEY (id_sensor) REFERENCES sensor(id_sensor),
    CONSTRAINT medicion_pkey PRIMARY KEY (id_medicion, fecha)
) PARTITION BY RANGE (fecha);

CREATE TABLE medicion_2016 PARTITION OF medicion FOR VALUES FROM ('2016-01-01') TO ('2017-01-01');
CREATE TABLE medicion_2017 PARTITION OF medicion FOR VALUES FROM ('2017-01-01') TO ('2018-01-01');
CREATE TABLE medicion_2018 PARTITION OF medicion FOR VALUES FROM ('2018-01-01') TO ('2019-01-01');
CREATE TABLE medicion_2019 PARTITION OF medicion FOR VALUES FROM ('2019-01-01') TO ('2020-01-01');
CREATE TABLE medicion_2020 PARTITION OF medicion FOR VALUES FROM ('2020-01-01') TO ('2021-01-01');
CREATE TABLE medicion_2021 PARTITION OF medicion FOR VALUES FROM ('2021-01-01') TO ('2022-01-01');
CREATE TABLE medicion_2022 PARTITION OF medicion FOR VALUES FROM ('2022-01-01') TO ('2023-01-01');
CREATE TABLE medicion_2023 PARTITION OF medicion FOR VALUES FROM ('2023-01-01') TO ('2024-01-01');
CREATE TABLE medicion_2024 PARTITION OF medicion FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
CREATE TABLE medicion_2025 PARTITION OF medicion FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
CREATE TABLE medicion_2026 PARTITION OF medicion FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');
CREATE TABLE medicion_default PARTITION OF medicion DEFAULT;

-- 8. INDICES (los de medicion se propagan a todas las particiones)
CREATE INDEX idx_medicion_fecha     ON medicion(fecha);
CREATE INDEX idx_medicion_sensor    ON medicion(id_sensor);
CREATE INDEX idx_medicion_pm25      ON medicion(pm25);
CREATE INDEX idx_sensor_zona        ON sensor(id_zona);
CREATE INDEX idx_sensor_organismo   ON sensor(id_organismo);
CREATE INDEX idx_zona_nombre        ON zona(nombre_zona);

-- 9. VISTA MATERIALIZADA
CREATE MATERIALIZED VIEW resumen_zonas AS
SELECT z.nombre_zona,
       AVG(m.pm25)             AS promedio_pm25,
       AVG(m.carros)           AS promedio_carros,
       COUNT(*)                AS total_mediciones,
       MAX(m.congestion_score) AS max_congestion
FROM medicion m
JOIN sensor s ON m.id_sensor = s.id_sensor
JOIN zona   z ON s.id_zona   = z.id_zona
GROUP BY z.nombre_zona;

CREATE INDEX idx_resumen_zonas ON resumen_zonas(nombre_zona);

-- 10. FUNCION ALMACENADA
CREATE OR REPLACE FUNCTION sensores_por_zona(p_zona VARCHAR)
RETURNS TABLE(nombre_sensor VARCHAR, tipo VARCHAR) AS $$
BEGIN
    RETURN QUERY
    SELECT s.nombre::VARCHAR, s.tipo_sensor::VARCHAR
    FROM sensor s
    JOIN zona z ON s.id_zona = z.id_zona
    WHERE z.nombre_zona = p_zona;
END;
$$ LANGUAGE plpgsql;

-- NOTA: la tabla resultado_spark_zonas NO se crea aqui. La genera Spark por
-- JDBC (modo overwrite) desde analisis_spark.ipynb. Documentarla en el informe.