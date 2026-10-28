-- ============================================================
-- 02_datos_referencia.sql
-- Datos maestros. Es IDEMPOTENTE: se puede ejecutar varias veces
-- sin duplicar filas (en tu base actual no cambia nada).
-- ============================================================

-- Ciudad
INSERT INTO ciudad (nombre) VALUES ('Smart City')
ON CONFLICT (nombre) DO NOTHING;

-- Categorias
INSERT INTO categoria_sensor (nombre_categoria) VALUES
    ('movilidad'), ('ambiente'), ('energia'), ('iot'), ('clima')
ON CONFLICT (nombre_categoria) DO NOTHING;

-- Organismos responsables (el orden fija ids 1..4 = MOPT, MINAE, Municipalidad, CNFL)
INSERT INTO organismo (nombre, responsable)
SELECT v.nombre, v.responsable
FROM (VALUES
    ('MOPT',          'Ministro de Obras Públicas'),
    ('MINAE',         'Ministro de Ambiente y Energía'),
    ('Municipalidad', 'Alcalde Municipal'),
    ('CNFL',          'Gerente de Energía')
) AS v(nombre, responsable)
WHERE NOT EXISTS (SELECT 1 FROM organismo o WHERE o.nombre = v.nombre);

-- Usuarios del sistema
INSERT INTO usuarios (nombre, correo) VALUES
    ('Admin SmartCity', 'admin@smartcity.cr'),
    ('Ana Mora',        'ana.mora@smartcity.cr'),
    ('Carlos Rojas',    'carlos.rojas@smartcity.cr'),
    ('María Solís',     'maria.solis@smartcity.cr')
ON CONFLICT (correo) DO NOTHING;

-- Sensor de prueba INACTIVO y sin mediciones.
-- Sirve para demostrar las consultas 3 (activos/inactivos) y 7 (sin actividad).
-- Ejecutar DESPUES de cargar zonas y sensores reales.
INSERT INTO sensor (nombre, tipo_sensor, estado, fecha_instalacion, id_zona, id_categoria, id_organismo)
SELECT 'S-TEST-INACTIVO', 'test', 'inactivo', DATE '2025-01-01',
       (SELECT MIN(id_zona)      FROM zona),
       (SELECT MIN(id_categoria) FROM categoria_sensor),
       (SELECT id_organismo FROM organismo WHERE nombre = 'Municipalidad')
WHERE (SELECT COUNT(*) FROM zona) > 0
ON CONFLICT (nombre) DO NOTHING;
