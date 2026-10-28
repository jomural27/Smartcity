-- ============================================================
-- 03_migraciones.sql
-- Lleva TU base actual al esquema final de 01_ddl.sql.
-- Ejecutar con "Ejecutar script" (Alt+X) para que la tabla temporal
-- y las transacciones vivan en la misma sesion.
-- SECCION A = historial (ya ejecutado, NO volver a correr).
-- SECCION B = pendiente (idempotente: se puede repetir sin dano).
-- ============================================================

-- ============================================================
-- SECCION A: HISTORIAL (ya ejecutado; solo documentacion)
-- ============================================================
-- A1. Tabla usuarios + 4 usuarios de ejemplo.
-- A2. sensor.fecha_instalacion (derivada de MIN(fecha) de cada sensor).
-- A3. zona.distrito (primera version, con lista fija; se corrige en B4).
-- A4. Particionamiento de medicion por RANGE(fecha): se creo
--     medicion_particionada, se copiaron las filas, se renombro
--     medicion -> medicion_backup y medicion_particionada -> medicion.
--     Particiones 2021..2026 + default.
-- A5. Bloque 1: 3FN en organismo (ya ejecutado y verificado: suma 285):
--     ALTER TABLE sensor ADD COLUMN id_organismo INTEGER;
--     UPDATE ... (asignar organismo por categoria)
--     ALTER TABLE organismo DROP COLUMN id_sensor;
--     ALTER TABLE sensor ALTER COLUMN id_organismo SET NOT NULL;
--     ALTER TABLE sensor ADD CONSTRAINT fk_sensor_organismo ...;
--     CREATE INDEX idx_sensor_organismo ON sensor(id_organismo);

-- ============================================================
-- SECCION B: PENDIENTE
-- ============================================================

-- B1. Fecha de instalacion del sensor de prueba
UPDATE sensor SET fecha_instalacion = DATE '2025-01-01'
WHERE nombre = 'S-TEST-INACTIVO' AND fecha_instalacion IS NULL;

-- B2. Particiones 2016-2020 y vaciado de medicion_default
--     (el aire empieza en 2016-03; sin estas particiones la mitad
--      de los datos cae en default y no se beneficia del pruning)
BEGIN;

CREATE TEMP TABLE tmp_default AS SELECT * FROM medicion_default;
DELETE FROM medicion_default;

CREATE TABLE IF NOT EXISTS medicion_2016 PARTITION OF medicion FOR VALUES FROM ('2016-01-01') TO ('2017-01-01');
CREATE TABLE IF NOT EXISTS medicion_2017 PARTITION OF medicion FOR VALUES FROM ('2017-01-01') TO ('2018-01-01');
CREATE TABLE IF NOT EXISTS medicion_2018 PARTITION OF medicion FOR VALUES FROM ('2018-01-01') TO ('2019-01-01');
CREATE TABLE IF NOT EXISTS medicion_2019 PARTITION OF medicion FOR VALUES FROM ('2019-01-01') TO ('2020-01-01');
CREATE TABLE IF NOT EXISTS medicion_2020 PARTITION OF medicion FOR VALUES FROM ('2020-01-01') TO ('2021-01-01');

INSERT INTO medicion SELECT * FROM tmp_default;
DROP TABLE tmp_default;

COMMIT;

-- B3. VERIFICACION (pegar estos resultados)
-- Esperado: particiones 2016..2026, default en 0 o ausente, ambos totales = 1,062,858
SELECT tableoid::regclass AS particion, COUNT(*) AS filas
FROM medicion GROUP BY 1 ORDER BY 1;

SELECT 'medicion' AS tabla, COUNT(*) AS filas FROM medicion
UNION ALL
SELECT 'medicion_backup', COUNT(*) FROM medicion_backup;

-- B4. Corregir distrito: CDMX si la zona tiene sensores de calidad_aire
UPDATE zona z
SET distrito = CASE
    WHEN EXISTS (SELECT 1 FROM sensor s
                 WHERE s.id_zona = z.id_zona
                   AND s.tipo_sensor = 'calidad_aire') THEN 'CDMX'
    ELSE 'SmartCity District'
END;

SELECT distrito, COUNT(*) AS zonas FROM zona GROUP BY distrito;

-- Revisar posible duplicado "FES Aragón" / "FES Aragon" (NO se corrige solo):
SELECT z.id_zona, z.nombre_zona, z.latitud, z.longitud, z.distrito,
       COUNT(s.id_sensor) AS sensores
FROM zona z LEFT JOIN sensor s ON s.id_zona = z.id_zona
WHERE z.nombre_zona ILIKE 'FES Arag%'
GROUP BY z.id_zona, z.nombre_zona, z.latitud, z.longitud, z.distrito;

-- B5. FK medicion -> sensor (se perdio al crear la tabla particionada)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint
                   WHERE conname = 'fk_medicion_sensor'
                     AND conrelid = 'medicion'::regclass) THEN
        ALTER TABLE medicion
            ADD CONSTRAINT fk_medicion_sensor
            FOREIGN KEY (id_sensor) REFERENCES sensor(id_sensor);
    END IF;
END $$;

-- B6. Borrar el respaldo. MANUAL: descomenta SOLO si en B3 ambos totales
--     fueron 1,062,858 y medicion_default quedo en 0.
-- DROP TABLE medicion_backup;

-- B7. Indices en la tabla padre (se propagan a todas las particiones).
--     Solo se crean si no existen ya.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE schemaname='public'
                   AND tablename='medicion' AND indexdef ILIKE '%(fecha)%') THEN
        CREATE INDEX ix_medicion_fecha ON medicion(fecha);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE schemaname='public'
                   AND tablename='medicion' AND indexdef ILIKE '%(id_sensor)%') THEN
        CREATE INDEX ix_medicion_sensor ON medicion(id_sensor);
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE schemaname='public'
                   AND tablename='medicion' AND indexdef ILIKE '%(pm25)%') THEN
        CREATE INDEX ix_medicion_pm25 ON medicion(pm25);
    END IF;
END $$;

-- B8. Secuencia de id_medicion al maximo actual (evita ids duplicados en futuros INSERT)
SELECT setval(pg_get_serial_sequence('medicion', 'id_medicion'),
              (SELECT MAX(id_medicion) FROM medicion));

-- B9. Estadisticas y vista materializada
ANALYZE medicion;
REFRESH MATERIALIZED VIEW resumen_zonas;

-- B10. Verificacion final de indices y FK de medicion
SELECT tablename, indexname FROM pg_indexes
WHERE schemaname = 'public' AND tablename = 'medicion' ORDER BY indexname;

SELECT conname, pg_get_constraintdef(oid) AS definicion
FROM pg_constraint WHERE conrelid = 'medicion'::regclass AND contype IN ('p','f');
