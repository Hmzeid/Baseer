#!/bin/sh
# Baseer backup: SQLite snapshot + evidence, timestamped.
# Run nightly (or before any upgrade). Restores by copying over data/.
# ROOT override for testing: BASEER_ROOT=/tmp/x sh ops/backup.sh
set -eu
ROOT="${BASEER_ROOT:-/Users/husseinabdelwahab/Ai/Baseer}"
STAMP=$(date +%Y%m%d-%H%M%S)
OUT="$ROOT/backups/baseer-$STAMP"
mkdir -p "$ROOT/backups"
mkdir -p "$OUT"
if [ -f "$ROOT/data/baseer.db" ]; then
  "$ROOT/.venv/bin/python" -c "
import sqlite3
src = sqlite3.connect('$ROOT/data/baseer.db')
dst = sqlite3.connect('$OUT/baseer.db')
src.backup(dst)
print('db snapshot ok')
"
fi
if [ -d "$ROOT/data/evidence" ]; then
  cp -R "$ROOT/data/evidence" "$OUT/evidence"
fi
ls -la "$OUT"
echo "backup done: $OUT"
