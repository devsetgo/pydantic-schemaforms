#!/usr/bin/env sh
# Kill processes listening on a TCP port (argument: port)
PORT="$1"
if [ -z "$PORT" ]; then
  echo "Usage: $0 <port>" >&2
  exit 2
fi
echo "Stopping any process running on port ${PORT}..."
pids=""
if command -v lsof >/dev/null 2>&1; then
  pids=$(lsof -ti tcp:${PORT} 2>/dev/null || true)
elif command -v fuser >/dev/null 2>&1; then
  pids=$(fuser -n tcp ${PORT} 2>/dev/null || true)
elif command -v ss >/dev/null 2>&1; then
  pids=$(ss -ltnp 2>/dev/null | grep -F ":${PORT}" || true | grep -o 'pid=[0-9]*' | sed 's/pid=//' | sort -u || true)
else
  pids=$(pgrep -f "uvicor[n] main:app.*--port ${PORT}" || true)
fi

# Normalize
pids=$(echo "${pids}" | tr ' ' '\n' | sed '/^$/d' | sort -u || true)

if [ -n "${pids}" ]; then
  echo "Found PIDs using port ${PORT}: ${pids}"
  echo "Sending TERM to ${pids}"
  echo "${pids}" | xargs -r kill -TERM || true
  sleep 1
  still=$(echo "${pids}" | xargs -r ps -o pid= -p 2>/dev/null || true)
  if [ -n "${still}" ]; then
    echo "Forcing kill for: ${still}"
    echo "${still}" | xargs -r kill -9 || true
  else
    echo "Processes terminated."
  fi
else
  echo "No process found running on port ${PORT}"
fi

echo "Port ${PORT} is now free"

# Fallback: try to find socket inode(s) for the port and map to PIDs via /proc
if [ -z "${pids}" ]; then
  PORT_HEX=$(printf "%04X" "$PORT")
  inodes=""
  for nf in /proc/net/tcp /proc/net/tcp6; do
    if [ -f "$nf" ]; then
      inodes="$inodes $(awk -v P="$PORT_HEX" 'NR>1 { split($2,a,":"); if(tolower(a[2])==tolower(P)) print $10 }' "$nf" 2>/dev/null || true)"
    fi
  done
  inodes=$(echo "$inodes" | tr ' ' '\n' | sed '/^$/d' | sort -u || true)
  if [ -n "$inodes" ]; then
    for ino in $inodes; do
      for piddir in /proc/[0-9]*; do
        pid=$(basename "$piddir")
        for fd in "$piddir"/fd/*; do
          if [ -L "$fd" ]; then
            tgt=$(readlink "$fd")
            if [ "$tgt" = "socket:[$ino]" ]; then
              pids="$pids $pid"
            fi
          fi
        done
      done
    done
  fi
  pids=$(echo "${pids}" | tr ' ' '\n' | sed '/^$/d' | sort -u || true)
  if [ -n "$pids" ]; then
    echo "(fallback) Found PIDs using port ${PORT}: $pids"
    echo "$pids" | xargs -r kill -TERM || true
    sleep 1
    still=$(echo "$pids" | xargs -r ps -o pid= -p 2>/dev/null || true)
    if [ -n "$still" ]; then
      echo "(fallback) Forcing kill for: $still"
      echo "$still" | xargs -r kill -9 || true
    fi
    echo "Port ${PORT} is now free (fallback)"
  fi
fi
