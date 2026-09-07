#!/bin/sh
set -u
export TMPDIR="$PWD/build/s2-execution/reviewer/tmp"
export TEMP="$TMPDIR" TMP="$TMPDIR"
export PIP_CACHE_DIR="$PWD/build/s2-execution/reviewer/cache"
export XDG_CACHE_HOME="$PWD/build/s2-execution/reviewer/cache/xdg"
export PYTHONPYCACHEPREFIX="$PWD/build/s2-execution/reviewer/cache/pycache"
PY="$PWD/build/s2-execution/reviewer/venv/bin/python"
E=docs/reviewer/evidence/V0.1/S2
"$PY" -m pytest --capture=sys -rP --basetemp=build/s2-execution/reviewer/tmp/full -o cache_dir=build/s2-execution/reviewer/cache/pytest > "$E/full.log" 2>&1
r=$?; printf 'full exit=%s\n' "$r"; [ "$r" = 0 ] || exit "$r"
"$PY" -m pytest --capture=sys -rP -m slow --basetemp=build/s2-execution/reviewer/tmp/slow -o cache_dir=build/s2-execution/reviewer/cache/pytest > "$E/slow.log" 2>&1
r=$?; printf 'slow exit=%s\n' "$r"; [ "$r" = 0 ] || exit "$r"
"$PY" "$E/independent.py" > "$E/independent.log" 2>&1
r=$?; printf 'independent exit=%s\n' "$r"; [ "$r" = 0 ] || exit "$r"
"$PY" "$E/longrun.py" > "$E/longrun.log" 2>&1
r=$?; printf 'longrun exit=%s\n' "$r"; exit "$r"
