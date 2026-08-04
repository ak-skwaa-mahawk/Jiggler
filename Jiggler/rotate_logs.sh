#!/usr/bin/env bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/telemetry.log"
MAX_BYTES=$((10 * 1024 * 1024)) # 10 MB limit
MAX_BACKUPS=5

if [ ! -f "$LOG_FILE" ]; then
    echo "Log file $LOG_FILE does not exist."
    exit 0
fi

# Get current log size in bytes
FILE_SIZE=$(wc -c < "$LOG_FILE" | xargs)

if [ "$FILE_SIZE" -ge "$MAX_BYTES" ]; then
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] 📦 Rotating $LOG_FILE ($(( FILE_SIZE / 1024 / 1024 )) MB >= 10 MB)..."

    # Shift older backup files (e.g., .4 -> .5, .3 -> .4)
    for i in $(seq $((MAX_BACKUPS - 1)) -1 1); do
        if [ -f "${LOG_FILE}.${i}" ]; then
            mv "${LOG_FILE}.${i}" "${LOG_FILE}.$((i + 1))"
        fi
    done

    # Move active log to .1
    mv "$LOG_FILE" "${LOG_FILE}.1"

    # Re-create fresh log file
    touch "$LOG_FILE"
    echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] 🚀 New telemetry log initialized after rotation." > "$LOG_FILE"
    echo "✅ Log rotation complete."
else
    echo "ℹ️ Log size is $(( FILE_SIZE / 1024 )) KB (Threshold: 10240 KB). No rotation needed."
fi
