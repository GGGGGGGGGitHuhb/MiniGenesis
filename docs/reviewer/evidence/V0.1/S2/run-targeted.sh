#!/bin/sh
set -eu
export TMPDIR="$PWD/build/s2-execution/reviewer/tmp" TEMP="$PWD/build/s2-execution/reviewer/tmp" TMP="$PWD/build/s2-execution/reviewer/tmp" PYTHONPYCACHEPREFIX="$PWD/build/s2-execution/reviewer/cache/pycache"
PY="$PWD/build/s2-execution/reviewer/venv/bin/python"
for expr in 'action or harvest or wait' 'lifecycle or death or age or metabolism' 'scheduler or determinism'; do
 "$PY" -m pytest --capture=sys -k "$expr" --basetemp=build/s2-execution/reviewer/tmp/targeted -o cache_dir=build/s2-execution/reviewer/cache/targeted
 done
