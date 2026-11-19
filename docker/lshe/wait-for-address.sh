#!/bin/sh
# Wait until the address Kolibri listens on (LSHE_BIND_IP in .env) is up on
# this server, so `docker compose up` can bind its ports. At boot Docker can
# start before the network has that address; binding then fails and Docker
# does not retry. Used by lshe-kolibri.service; exits 0 at once when Kolibri
# listens on every address (LSHE_BIND_IP empty or 0.0.0.0).
#
#   ./wait-for-address.sh [seconds]     (default 120)

cd "$(dirname "$0")" || exit 1
limit="${1:-120}"
ip=$(sed -n 's/^LSHE_BIND_IP=//p' .env 2>/dev/null | tail -1 | tr -d '"'"'"' \r')

# Every address, or a loopback one (127.x is always up): nothing to wait for.
case "$ip" in
  "" | 0.0.0.0 | 127.*) exit 0 ;;
esac

waited=0
while [ "$waited" -lt "$limit" ]; do
  if ip -o addr show 2>/dev/null | grep -q " inet $ip/"; then
    [ "$waited" -gt 0 ] && echo "address $ip is up after ${waited}s"
    exit 0
  fi
  sleep 2
  waited=$((waited + 2))
done

echo "address $ip (LSHE_BIND_IP) is not on this server after ${limit}s;" \
  "check the network cable or Wi-Fi, and LSHE_BIND_IP in .env" >&2
exit 1
