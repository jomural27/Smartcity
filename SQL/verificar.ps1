# verificar.ps1 (v2)
# Ejecutar desde la carpeta Smartcity (la que contiene sql\):
#   powershell -ExecutionPolicy Bypass -File .\sql\verificar.ps1
# NO toca la base "smartcity": trabaja con copias (smartcity_test, smartcity_vacia).

$lineas  = New-Object System.Collections.Generic.List[string]
$resumen = New-Object System.Collections.Generic.List[string]

function Log([string]$texto) {
    $lineas.Add($texto)
    Write-Host $texto
}

# Ejecuta una sentencia SQL (argumentos directos, sin sh -c: evita problemas de comillas)
function Sql([string]$dbname, [string]$sql) {
    docker exec -e PGPASSWORD=admin123 postgres psql -U admin -d $dbname -t -c $sql 2>&1 |
        ForEach-Object { "$_" }
}

function Run-File([string]$archivo, [string]$dbname, [string]$stop) {
    docker cp "sql\$archivo" "postgres:/tmp/$archivo" | Out-Null
    Log ""
    Log "=================== $archivo  (base: $dbname) ==================="
    $salida = docker exec -e PGPASSWORD=admin123 postgres psql -U admin -d $dbname -v "ON_ERROR_STOP=$stop" --echo-errors -f "/tmp/$archivo" 2>&1 |
        ForEach-Object { "$_" }
    foreach ($l in $salida) { Log $l }
    $errores = @($salida | Where-Object { $_ -match "ERROR|psql: error" })
    if ($errores.Count -eq 0) { $r = ">>> $archivo : SIN ERRORES" }
    else                      { $r = ">>> $archivo : $($errores.Count) LINEA(S) CON ERROR" }
    Log $r
    $resumen.Add($r)
}

# 0. Docker
Log "0. Estado de Docker"
$ps = docker ps --filter "name=postgres" --format "{{.Names}} {{.Status}}"
Log "$ps"
if (-not $ps) { Log "El contenedor postgres no esta corriendo. Ejecuta: docker compose up -d postgres"; exit 1 }

# 1. Copia de la base real
Log "`n1. Creando copia smartcity_test"
Sql "postgres" "DROP DATABASE IF EXISTS smartcity_test" | ForEach-Object { Log $_ }
Sql "postgres" "CREATE DATABASE smartcity_test"         | ForEach-Object { Log $_ }
docker exec -e PGPASSWORD=admin123 postgres sh -c "pg_dump -U admin -d smartcity | psql -U admin -d smartcity_test -q" 2>&1 |
    ForEach-Object { "$_" } | Where-Object { $_ -match "ERROR" } | ForEach-Object { Log $_ }
Log "Filas de medicion en la copia (debe ser 1062858):"
Sql "smartcity_test" "SELECT COUNT(*) FROM medicion" | ForEach-Object { Log $_ }

# 2. DDL en base vacia
Log "`n2. Probando 01_ddl.sql en base VACIA"
Sql "postgres" "DROP DATABASE IF EXISTS smartcity_vacia" | ForEach-Object { Log $_ }
Sql "postgres" "CREATE DATABASE smartcity_vacia"         | ForEach-Object { Log $_ }
Run-File "01_ddl.sql" "smartcity_vacia" "1"

# 3. Resto de archivos sobre la copia
foreach ($f in @("03_migraciones.sql","02_datos_referencia.sql","04_consultas_obligatorias.sql","05_consultas_avanzadas.sql","06_rendimiento.sql")) {
    Run-File $f "smartcity_test" "0"
}

# 4. Limpieza
Log "`n4. Limpieza"
Sql "postgres" "DROP DATABASE IF EXISTS smartcity_test"  | ForEach-Object { Log $_ }
Sql "postgres" "DROP DATABASE IF EXISTS smartcity_vacia" | ForEach-Object { Log $_ }

# 5. Resumen
Log "`n=================== RESUMEN ==================="
foreach ($r in $resumen) { Log $r }

# Escribir el reporte UNA sola vez (primero fuera de OneDrive, luego copiar)
$tmp = Join-Path $env:TEMP "reporte_verificacion.txt"
$lineas | Set-Content -Path $tmp -Encoding utf8
Write-Host "`nReporte guardado en: $tmp"
try {
    Copy-Item $tmp "sql\reporte_verificacion.txt" -Force -ErrorAction Stop
    Write-Host "Copia tambien en: sql\reporte_verificacion.txt"
} catch {
    Write-Host "(No se pudo copiar a sql\ por OneDrive; usa la ruta de TEMP de arriba)"
}