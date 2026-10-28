-- ============================================================
-- 05_consultas_avanzadas.sql
-- Consultas basicas, avanzadas y preguntas de ejemplo del enunciado.
-- Datos: aire 2016-2026 (OpenAQ, solo pm25/pm10/no2/o3/co);
--        trafico 2026-01..2026-03 (carros, temperatura, congestion).
-- ============================================================

-- ---------- A. BASICAS: SELECT / WHERE / ORDER BY / DISTINCT ----------
SELECT nombre, tipo_sensor, fecha_instalacion
FROM sensor
WHERE estado = 'activo' AND tipo_sensor = 'calidad_aire'
ORDER BY fecha_instalacion, nombre
LIMIT 20;

SELECT DISTINCT distrito FROM zona ORDER BY distrito;
SELECT DISTINCT tipo_sensor, estado FROM sensor ORDER BY tipo_sensor, estado;

-- ---------- B. JOINS (INNER y LEFT) ----------
-- INNER JOIN multiple: sensor + zona + categoria + organismo
SELECT s.nombre AS sensor, z.nombre_zona, c.nombre_categoria, o.nombre AS organismo
FROM sensor s
INNER JOIN zona z             ON z.id_zona = s.id_zona
INNER JOIN categoria_sensor c ON c.id_categoria = s.id_categoria
INNER JOIN organismo o        ON o.id_organismo = s.id_organismo
ORDER BY z.nombre_zona, s.nombre
LIMIT 20;

-- LEFT JOIN: zonas sin ningun sensor
SELECT z.nombre_zona
FROM zona z
LEFT JOIN sensor s ON s.id_zona = z.id_zona
WHERE s.id_sensor IS NULL;

-- ---------- C. AGREGADOS: COUNT, SUM, AVG, MIN, MAX, HAVING ----------
SELECT z.nombre_zona,
       COUNT(*)                          AS mediciones,
       SUM(m.carros)                     AS total_vehiculos,
       ROUND(AVG(m.temperatura)::numeric, 1) AS temp_prom,
       MIN(m.temperatura)                AS temp_min,
       MAX(m.temperatura)                AS temp_max
FROM medicion m
JOIN sensor s ON s.id_sensor = m.id_sensor
JOIN zona z   ON z.id_zona = s.id_zona
WHERE m.carros IS NOT NULL
GROUP BY z.nombre_zona
HAVING COUNT(*) > 1000
ORDER BY total_vehiculos DESC;

-- ---------- D. SUBCONSULTA ----------
SELECT nombre, tipo_sensor
FROM sensor
WHERE id_sensor IN (SELECT DISTINCT id_sensor FROM medicion WHERE pm25 > 100)
ORDER BY nombre;

-- ---------- E. CTE ----------
-- Zonas con pm25 promedio superior al promedio de todas las zonas
WITH promedio_por_zona AS (
    SELECT z.nombre_zona, AVG(m.pm25) AS promedio_pm25
    FROM zona z
    JOIN sensor s ON s.id_zona = z.id_zona
    JOIN medicion m ON m.id_sensor = s.id_sensor
    WHERE m.pm25 IS NOT NULL
    GROUP BY z.nombre_zona
)
SELECT nombre_zona, ROUND(promedio_pm25::numeric, 2) AS promedio_pm25
FROM promedio_por_zona
WHERE promedio_pm25 > (SELECT AVG(promedio_pm25) FROM promedio_por_zona)
ORDER BY promedio_pm25 DESC;

-- ---------- F. FUNCIONES DE VENTANA ----------
-- F1. Promedio movil de 7 dias del pm25 por zona (solo 2021; usa pruning)
WITH diario AS (
    SELECT z.nombre_zona, m.fecha::date AS dia, AVG(m.pm25) AS pm25_dia
    FROM medicion m
    JOIN sensor s ON s.id_sensor = m.id_sensor
    JOIN zona z   ON z.id_zona = s.id_zona
    WHERE m.pm25 IS NOT NULL
      AND m.fecha >= '2021-01-01' AND m.fecha < '2022-01-01'
    GROUP BY z.nombre_zona, m.fecha::date
)
SELECT nombre_zona, dia,
       ROUND(pm25_dia::numeric, 2) AS pm25_dia,
       ROUND(AVG(pm25_dia) OVER (PARTITION BY nombre_zona ORDER BY dia
             ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)::numeric, 2) AS promedio_movil_7d
FROM diario
ORDER BY nombre_zona, dia
LIMIT 60;

-- F2. LAG: variacion mensual del pm25 por zona (2021)
--     El cambio solo se calcula si el mes anterior existe (los datos tienen huecos);
--     si falta un mes, la columna queda en NULL en vez de comparar contra uno lejano.
WITH mensual AS (
    SELECT z.nombre_zona,
           date_trunc('month', m.fecha)::date AS mes,
           AVG(m.pm25) AS pm25_mes
    FROM medicion m
    JOIN sensor s ON s.id_sensor = m.id_sensor
    JOIN zona z   ON z.id_zona = s.id_zona
    WHERE m.pm25 IS NOT NULL
      AND m.fecha >= '2021-01-01' AND m.fecha < '2022-01-01'
    GROUP BY z.nombre_zona, date_trunc('month', m.fecha)
)
SELECT nombre_zona, mes,
       ROUND(pm25_mes::numeric, 2) AS pm25_mes,
       CASE WHEN LAG(mes) OVER w = (mes - INTERVAL '1 month')::date
            THEN ROUND((pm25_mes - LAG(pm25_mes) OVER w)::numeric, 2)
       END AS cambio_vs_mes_anterior
FROM mensual
WINDOW w AS (PARTITION BY nombre_zona ORDER BY mes)
ORDER BY nombre_zona, mes
LIMIT 60;

-- F3. RANK dentro de cada distrito
SELECT distrito, nombre_zona, pm25_prom,
       RANK() OVER (PARTITION BY distrito ORDER BY pm25_prom DESC) AS rank_en_distrito
FROM (
    SELECT z.distrito, z.nombre_zona, ROUND(AVG(m.pm25)::numeric, 2) AS pm25_prom
    FROM medicion m
    JOIN sensor s ON s.id_sensor = m.id_sensor
    JOIN zona z   ON z.id_zona = s.id_zona
    WHERE m.pm25 IS NOT NULL
    GROUP BY z.distrito, z.nombre_zona
) t
ORDER BY distrito, rank_en_distrito
LIMIT 30;

-- ---------- G. CONSULTAS SOBRE FECHAS ----------
-- Mediciones por mes durante 2024 (solo lee la particion medicion_2024)
SELECT date_trunc('month', fecha)::date AS mes, COUNT(*) AS mediciones
FROM medicion
WHERE fecha >= '2024-01-01' AND fecha < '2025-01-01'
GROUP BY 1
ORDER BY 1;

-- Mediciones por anio (todo el historico)
SELECT EXTRACT(YEAR FROM fecha)::int AS anio, COUNT(*) AS mediciones
FROM medicion
GROUP BY 1
ORDER BY 1;

-- Consulta que aprovecha el indice por sensor + rango de fecha
SELECT fecha, pm25, pm10
FROM medicion
WHERE id_sensor = (SELECT MIN(id_sensor) FROM sensor WHERE tipo_sensor = 'calidad_aire')
  AND fecha >= '2021-01-01' AND fecha < '2021-02-01'
ORDER BY fecha
LIMIT 50;

-- ---------- H. PREGUNTAS DE EJEMPLO DEL ENUNCIADO ----------
-- H1. Zona con mayor cantidad de vehiculos
SELECT z.nombre_zona, SUM(m.carros) AS total_vehiculos
FROM medicion m
JOIN sensor s ON s.id_sensor = m.id_sensor
JOIN zona z   ON z.id_zona = s.id_zona
WHERE m.carros IS NOT NULL
GROUP BY z.nombre_zona
ORDER BY total_vehiculos DESC
LIMIT 5;

-- H2. Temperatura promedio por zona (solo trafico tiene temperatura)
SELECT z.nombre_zona, ROUND(AVG(m.temperatura)::numeric, 2) AS temperatura_prom
FROM medicion m
JOIN sensor s ON s.id_sensor = m.id_sensor
JOIN zona z   ON z.id_zona = s.id_zona
WHERE m.temperatura IS NOT NULL
GROUP BY z.nombre_zona
ORDER BY temperatura_prom DESC;

-- H3. Hora de mayor congestion
SELECT EXTRACT(HOUR FROM fecha)::int AS hora,
       ROUND(AVG(congestion_score)::numeric, 2) AS congestion_prom,
       ROUND(AVG(carros)::numeric, 1)           AS carros_prom
FROM medicion
WHERE congestion_score IS NOT NULL
GROUP BY 1
ORDER BY congestion_prom DESC
LIMIT 5;

-- H4. Zona con mayor contaminacion (pm25)
SELECT z.nombre_zona, ROUND(AVG(m.pm25)::numeric, 2) AS pm25_prom, COUNT(*) AS lecturas
FROM medicion m
JOIN sensor s ON s.id_sensor = m.id_sensor
JOIN zona z   ON z.id_zona = s.id_zona
WHERE m.pm25 IS NOT NULL
GROUP BY z.nombre_zona
HAVING COUNT(*) > 1000
ORDER BY pm25_prom DESC
LIMIT 5;

-- H5. Sensores que dejaron de enviar informacion
--     (ultima medicion mas de 30 dias antes de la medicion mas reciente de toda la red)
WITH ult AS (
    SELECT id_sensor, MAX(fecha) AS ultima FROM medicion GROUP BY id_sensor
), ref AS (
    SELECT MAX(fecha) AS max_global FROM medicion
)
SELECT s.nombre, s.tipo_sensor, z.nombre_zona, u.ultima,
       (ref.max_global::date - u.ultima::date) AS dias_sin_datos
FROM sensor s
JOIN zona z ON z.id_zona = s.id_zona
LEFT JOIN ult u ON u.id_sensor = s.id_sensor
CROSS JOIN ref
WHERE u.ultima IS NULL OR u.ultima < ref.max_global - INTERVAL '30 days'
ORDER BY u.ultima NULLS FIRST
LIMIT 30;