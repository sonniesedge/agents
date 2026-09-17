# Token Budget

At the start of any new session check the remaining token budget. At the next prompt only proceed if there are clearly enough tokens to complete the task.

Get the remaining per-day credits using the following command:

```sh
d=$(date +%d); m=$(date +%m); y=$(date +%Y); last=$(date -jv+1m -v1d -v-1d -f "%Y-%m-%d" "$y-$m-01" +%d); c=0; for i in $(seq $d $last); do [ "$(date -j -f "%Y-%m-%d" "$y-$m-$(printf %02d $i)" +%u)" -le 5 ] && c=$((c+1)); done; if command -v occe >/dev/null 2>&1; then printf '%.1f credits per remaining working day (%d working days left, including today)\n' "$(echo "$(occe --remaining)/$c" | bc -l)" "$c"; else printf 'occe binary is not installed: credit budget unknown (%d working days left, including today)\n' "$c"; fi
```
