BEGIN { FS="\t" }
function flush() { printf "%s\tcount=%d\tavg=%.2f\tmin=%s\tmax=%s\n", k, n, s/n, mn, mx }
{
  if (NR > 1 && $1 != k) { flush(); n = 0; s = 0 }
  if (n == 0) { mn = $2; mx = $2 }
  k = $1; n++; s += $2
  if ($2+0 < mn+0) mn = $2
  if ($2+0 > mx+0) mx = $2
}
END { if (NR > 0) flush() }