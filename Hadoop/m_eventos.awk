BEGIN { FS="," }
$1 != "sensor_nombre" && ($15 == "1" || $15 == "True") { print $2 "\t1" }