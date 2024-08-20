#!/usr/bin/env bash
# Use this script to test if a given TCP host/port are available using telnet

TIMEOUT=60
HOST="$1"
PORT="$2"

if [ -z "$HOST" ] || [ -z "$PORT" ]; then
    echo "Usage: $0 <host> <port>"
    exit 1
fi

echo "Waiting for $HOST:$PORT to be available..."

for i in `seq $TIMEOUT` ; do
    echo "Attempt $i: Checking connection to $HOST:$PORT..."
    (echo > /dev/tcp/$HOST/$PORT) >/dev/null 2>&1
    result=$?
    if [ $result -eq 0 ] ; then
        echo "Connection to $HOST:$PORT succeeded."
        exit 0
    fi
    echo "Attempt $i: Connection to $HOST:$PORT failed."
    sleep 1
done

echo "Operation timed out after $TIMEOUT seconds" >&2
exit 1
