BEGIN { FS="\t" }
{ if (NR > 1 && $1 != k) { print k "\t" s; s = 0 } k = $1; s += $2 }
END { if (NR > 0) print k "\t" s }