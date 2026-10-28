#!/bin/sh
# Baseer LAN TLS: self-signed certificate for on-site HTTPS.
# Browsers will show a trust warning on first visit (expected for a
# self-signed LAN cert) — for remote access prefer the site VPN instead.
# Usage:
#   sh ops/tls.sh [hostname]     # writes data/tls/cert.pem + key.pem
#   # then run uvicorn with:
#   ../.venv/bin/python -m uvicorn app:app --port 8001 \
#     --ssl-certfile ../data/tls/cert.pem --ssl-keyfile ../data/tls/key.pem
set -eu
ROOT="${BASEER_ROOT:-/Users/husseinabdelwahab/Ai/Baseer}"
HOST="${1:-$(hostname)}"
OUT="$ROOT/data/tls"
mkdir -p "$OUT"
if [ -f "$OUT/cert.pem" ]; then
  echo "exists: $OUT/cert.pem (delete to regenerate)"
  exit 0
fi
openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout "$OUT/key.pem" -out "$OUT/cert.pem" -days 825 \
  -subj "/CN=$HOST" -addext "subjectAltName=DNS:$HOST,DNS:localhost,IP:127.0.0.1" 2>/dev/null
chmod 600 "$OUT/key.pem"
ls -la "$OUT"
echo "done for host: $HOST"
