#!/bin/sh
# Fix ownership of bind-mounted /data (often created root-owned by the host), then drop to uid 10001.
set -e
if [ "$(id -u)" = "0" ]; then
  mkdir -p "$BLOOMERY_DATA_DIR"
  chown -R bloomery:bloomery "$BLOOMERY_DATA_DIR"
  exec setpriv --reuid=bloomery --regid=bloomery --init-groups "$@"
fi
exec "$@"
