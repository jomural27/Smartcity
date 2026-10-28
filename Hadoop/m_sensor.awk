BEGIN { FS="," }
$1 != "sensor_nombre" { print $1 "\t1" }