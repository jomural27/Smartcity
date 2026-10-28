BEGIN { FS="," }
$1 != "sensor_nombre" && $11 != "" { print "global\t" $11 }