BEGIN { FS="," }
$1 != "sensor_nombre" && $9 != "" {
  d = substr($3, 1, 10)
  if (d >= ini && d <= fin) print $1 "\t" $9
}