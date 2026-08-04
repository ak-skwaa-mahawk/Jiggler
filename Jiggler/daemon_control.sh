#!/usr/bin/env bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="${SCRIPT_DIR}/../Platform/venv/bin/python3"
CLIENT_SCRIPT="${SCRIPT_DIR}/stream_client.py"
PID_FILE="${SCRIPT_DIR}/stream_client.pid"
MONITOR_PID_FILE="${SCRIPT_DIR}/monitor.pid"
LOG_FILE="${SCRIPT_DIR}/telemetry.log"
ROTATE_SCRIPT="${SCRIPT_DIR}/rotate_logs.sh"

TARGET_FPS=60
BATCH_SIZE=1000000
MIN_FPS_THRESHOLD=40.0
HEALTH_CHECK_INTERVAL=5

get_pid() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            echo "$pid"
            return 0
        fi
    fi
    echo ""
}

get_monitor_pid() {
    if [ -f "$MONITOR_PID_FILE" ]; then
        local pid=$(cat "$MONITOR_PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            echo "$pid"
            return 0
        fi
    fi
    echo ""
}

start_daemon() {
    local pid=$(get_pid)
    if [ -n "$pid" ]; then
        echo "⚠️ Stream client is already running (PID: ${pid})."
        return 0
    fi

    echo "🚀 Starting stream_client.py daemon (FPS: ${TARGET_FPS}, Batch: ${BATCH_SIZE})..."
    nohup "$VENV_PYTHON" "$CLIENT_SCRIPT" \
        --fps "$TARGET_FPS" \
        --batch-size "$BATCH_SIZE" \
        --log-file "$LOG_FILE" > /dev/null 2>&1 &

    local new_pid=$!
    echo "$new_pid" > "$PID_FILE"
    
    sleep 1
    if kill -0 "$new_pid" 2>/dev/null; then
        echo "✅ Daemon started successfully (PID: ${new_pid})."
    else
        echo "❌ Failed to start daemon. Check telemetry log for details."
        rm -f "$PID_FILE"
    fi
}

stop_daemon() {
    local pid=$(get_pid)
    if [ -z "$pid" ]; then
        echo "ℹ️ Stream client is not running."
        rm -f "$PID_FILE"
        return 0
    fi

    echo "⏹️ Stopping stream_client.py daemon (PID: ${pid})..."
    kill -SIGTERM "$pid" 2>/dev/null

    local count=0
    while kill -0 "$pid" 2>/dev/null && [ $count -lt 50 ]; do
        sleep 0.1
        count=$((count + 1))
    done

    if kill -0 "$pid" 2>/dev/null; then
        echo "⚠️ Process did not terminate gracefully; sending SIGKILL..."
        kill -9 "$pid" 2>/dev/null
    fi

    rm -f "$PID_FILE"
    echo "✅ Daemon stopped."
}

run_healthcheck() {
    local pid=$(get_pid)
    if [ -z "$pid" ]; then
        echo "🔴 Healthcheck failed: Stream daemon is NOT running."
        return 1
    fi

    if [ ! -f "$LOG_FILE" ]; then
        echo "⚠️ Log file not found. Skipping metric evaluation."
        return 0
    fi

    local last_report=$(grep "FPS:" "$LOG_FILE" | tail -n 1)
    if [ -z "$last_report" ]; then
        echo "⚠️ No recent FPS telemetry entries found."
        return 0
    fi

    local current_fps=$(echo "$last_report" | awk -F'FPS:' '{print $2}' | awk -F'/' '{print $1}' | xargs)

    if [ -n "$current_fps" ]; then
        local is_healthy=$(python3 -c "print(1 if float('${current_fps}') >= ${MIN_FPS_THRESHOLD} else 0)" 2>/dev/null)
        if [ "$is_healthy" -eq 1 ]; then
            echo "🟢 Healthcheck passed: FPS is nominal (${current_fps} >= threshold ${MIN_FPS_THRESHOLD})."
            return 0
        else
            echo "⚠️ Healthcheck FAILED: FPS degraded (${current_fps} < threshold ${MIN_FPS_THRESHOLD}). Restarting..."
            stop_daemon
            sleep 1
            start_daemon
            return 2
        fi
    fi
    return 0
}

start_monitor() {
    local mpid=$(get_monitor_pid)
    if [ -n "$mpid" ]; then
        echo "⚠️ Health monitor daemon is already running (PID: ${mpid})."
        return 0
    fi

    echo "🛡️ Starting continuous health monitor & auto-rotator (Interval: ${HEALTH_CHECK_INTERVAL}s)..."
    (
        while true; do
            sleep "$HEALTH_CHECK_INTERVAL"
            
            # 1. Run log rotator check
            if [ -x "$ROTATE_SCRIPT" ]; then
                "$ROTATE_SCRIPT" > /dev/null 2>&1
            fi

            # 2. Run FPS health check
            local pid=$(get_pid)
            if [ -n "$pid" ] && [ -f "$LOG_FILE" ]; then
                local last_report=$(grep "FPS:" "$LOG_FILE" | tail -n 1)
                if [ -n "$last_report" ]; then
                    local current_fps=$(echo "$last_report" | awk -F'FPS:' '{print $2}' | awk -F'/' '{print $1}' | xargs)
                    if [ -n "$current_fps" ]; then
                        local is_healthy=$(python3 -c "print(1 if float('${current_fps}') >= ${MIN_FPS_THRESHOLD} else 0)" 2>/dev/null)
                        if [ "$is_healthy" -ne 1 ]; then
                            echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] 🚨 Monitor Trigger: FPS drop detected (${current_fps} FPS). Triggering auto-recovery..." >> "$LOG_FILE"
                            stop_daemon > /dev/null 2>&1
                            sleep 1
                            start_daemon > /dev/null 2>&1
                        fi
                    fi
                fi
            fi
        done
    ) > /dev/null 2>&1 &

    local new_mpid=$!
    echo "$new_mpid" > "$MONITOR_PID_FILE"
    echo "✅ Health monitor & auto-rotator daemon started (PID: ${new_mpid})."
}

stop_monitor() {
    local mpid=$(get_monitor_pid)
    if [ -n "$mpid" ]; then
        echo "⏹️ Stopping health monitor daemon (PID: ${mpid})..."
        kill -9 "$mpid" 2>/dev/null
        rm -f "$MONITOR_PID_FILE"
        echo "✅ Monitor stopped."
    else
        echo "ℹ️ Health monitor daemon is not running."
    fi
}

status_daemon() {
    local pid=$(get_pid)
    local mpid=$(get_monitor_pid)

    if [ -n "$pid" ]; then
        echo "🟢 Stream Daemon: RUNNING (PID: ${pid})"
    else
        echo "🔴 Stream Daemon: STOPPED"
    fi

    if [ -n "$mpid" ]; then
        echo "🛡️ Health Monitor: ACTIVE (PID: ${mpid})"
    else
        echo "⚪ Health Monitor: INACTIVE"
    fi

    if [ -f "$LOG_FILE" ]; then
        echo "--- Recent Telemetry ---"
        tail -n 5 "$LOG_FILE"
    fi
}

case "$1" in
    start)
        start_daemon
        ;;
    stop)
        stop_monitor
        stop_daemon
        ;;
    restart)
        stop_daemon
        sleep 1
        start_daemon
        ;;
    status)
        status_daemon
        ;;
    healthcheck)
        run_healthcheck
        ;;
    start-monitor)
        start_daemon
        start_monitor
        ;;
    stop-monitor)
        stop_monitor
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|healthcheck|start-monitor|stop-monitor}"
        exit 1
        ;;
esac
