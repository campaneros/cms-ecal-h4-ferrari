#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGFILE="$HOME/kinit_expect_loop.log"

while true; do
  echo "$(date): running kinit via expect" >> "$LOGFILE"
  if "$SCRIPT_DIR/kinit_expect.sh" >> "$LOGFILE" 2>&1; then
    echo "$(date): kinit OK" >> "$LOGFILE"
  else
    echo "$(date): kinit FAILED" >> "$LOGFILE"
  fi
  sleep $((20 * 3600))
done
