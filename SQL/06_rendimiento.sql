-- ============================================================
-- 06_rendimiento.sql
-- Evidencia de indices y partition pruning (objetivo 4 del enunciado).
-- Ejecuta cada EXPLAIN por separado y guarda captura del plan.
-- Ejecutar DESPUES de 03_migraciones.sql (necesita particiones e indices).
-- ============================================================
ANALYZE medicion;

-- 1. SIN indice (forzando scan secuencial)
SET enable_indexscan = off;
SET enable_bitmapscan = off;
SET enable_indexonlyscan = off;
EXPLAIN (ANALYZE, BUFFERS)
SELECT COUNT(*) FROM medicion WHERE pm25 > 50;

-- 2. CON indice
RESET enable_indexscan;
RESET enable_bitmapscan;
RESET enable_indexonlyscan;
EXPLAIN (ANALYZE, BUFFERS)
SELECT COUNT(*) FROM medicion WHERE pm25 > 50;

-- 3. PARTITION PRUNING: solo debe aparecer medicion_2024 en el plan
EXPLAIN (ANALYZE, BUFFERS)
SELECT COUNT(*) FROM medicion
WHERE fecha >= '2024-01-01' AND fecha < '2024-02-01';

-- 4. Sin filtro de fecha: recorre TODAS las particiones (para comparar con el 3)
EXPLAIN (ANALYZE, BUFFERS)
SELECT COUNT(*) FROM medicion WHERE pm25 > 50 AND fecha IS NOT NULL;

-- 5. Indice por sensor + fecha
EXPLAIN (ANALYZE, BUFFERS)
SELECT fecha, pm25
FROM medicion
WHERE id_sensor = (SELECT MIN(id_sensor) FROM sensor WHERE tipo_sensor = 'calidad_aire')
  AND fecha >= '2021-01-01' AND fecha < '2021-02-01'
ORDER BY fecha;

-- 6. JOIN + agregacion sobre todo el volumen
EXPLAIN (ANALYZE, BUFFERS)
SELECT z.nombre_zona, AVG(m.pm25) AS pm25_prom
FROM medicion m
JOIN sensor s ON s.id_sensor = m.id_sensor
JOIN zona z   ON z.id_zona = s.id_zona
WHERE m.pm25 IS NOT NULL
GROUP BY z.nombre_zona
ORDER BY pm25_prom DESC;

-- 7. Tamano por particion (para el informe)
SELECT inhrelid::regclass AS particion,
       pg_size_pretty(pg_total_relation_size(inhrelid)) AS tamano
FROM pg_inherits
WHERE inhparent = 'medicion'::regclass
ORDER BY 1;
