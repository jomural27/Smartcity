-- ============================================================
-- 04_consultas_obligatorias.sql
-- Las 10 consultas obligatorias de PostgreSQL (enunciado, seccion 5a).
-- Ejecutar DESPUES de 03_migraciones.sql.
-- ============================================================

-- 1. SENSORES POR TIPO
SELECT tipo_sensor, COUNT(*) AS cantidad
FROM sensor
GROUP BY tipo_sensor
ORDER BY cantidad DESC;

-- 2. SENSORES POR UBICACION (LEFT JOIN: incluye zonas sin sensores)
SELECT z.nombre_zona, z.distrito, COUNT(s.id_sensor) AS cantidad_sensores
FROM zona z
LEFT JOIN sensor s ON s.id_zona = z.id_zona
GROUP BY z.nombre_zona, z.distrito
ORDER BY cantidad_sensores DESC, z.nombre_zona;

-- 3. SENSORES ACTIVOS E INACTIVOS
SELECT estado, COUNT(*) AS cantidad
FROM sensor
GROUP BY estado
ORDER BY cantidad DESC;

-- 4. SENSORES POR ORGANISMO RESPONSABLE
SELECT o.nombre AS organismo, o.responsable, COUNT(s.id_sensor) AS sensores_asignados
FROM organismo o
LEFT JOIN sensor s ON s.id_organismo = o.id_organismo
GROUP BY o.nombre, o.responsable
ORDER BY sensores_asignados DESC;

-- 5. UBICACIONES CON MAYOR CANTIDAD DE SENSORES
SELECT z.nombre_zona, COUNT(s.id_sensor) AS total_sensores
FROM zona z
JOIN sensor s ON s.id_zona = z.id_zona
GROUP BY z.nombre_zona
ORDER BY total_sensores DESC
LIMIT 10;

-- 6. SENSORES INSTALADOS POR ANIO
-- (fecha_instalacion se derivo de la primera medicion de cada sensor)
SELECT EXTRACT(YEAR FROM fecha_instalacion)::int AS anio,
       COUNT(*) AS sensores_instalados
FROM sensor
WHERE fecha_instalacion IS NOT NULL
GROUP BY 1
ORDER BY 1;

-- 7. SENSORES SIN ACTIVIDAD REGISTRADA (ninguna medicion)
SELECT s.nombre, s.tipo_sensor, s.estado, z.nombre_zona
FROM sensor s
JOIN zona z ON z.id_zona = s.id_zona
WHERE NOT EXISTS (SELECT 1 FROM medicion m WHERE m.id_sensor = s.id_sensor);

-- 8. RANKING DE ZONAS MONITOREADAS (funcion de ventana RANK)
SELECT z.nombre_zona,
       COUNT(m.id_medicion) AS total_mediciones,
       ROUND(AVG(m.pm25)::numeric, 2) AS promedio_pm25,
       RANK() OVER (ORDER BY COUNT(m.id_medicion) DESC) AS ranking
FROM zona z
JOIN sensor s ON s.id_zona = z.id_zona
JOIN medicion m ON m.id_sensor = s.id_sensor
GROUP BY z.nombre_zona
ORDER BY ranking
LIMIT 15;

-- 9. CONSULTA USANDO LA VISTA MATERIALIZADA
SELECT nombre_zona,
       ROUND(promedio_pm25::numeric, 2)   AS promedio_pm25,
       ROUND(promedio_carros::numeric, 1) AS promedio_carros,
       total_mediciones, max_congestion
FROM resumen_zonas
ORDER BY promedio_pm25 DESC NULLS LAST
LIMIT 10;

-- 10. CONSULTA USANDO LA FUNCION ALMACENADA
SELECT * FROM sensores_por_zona('Financial District');   -- zona de trafico
SELECT * FROM sensores_por_zona('Santa Fe');             -- zona de calidad del aire
