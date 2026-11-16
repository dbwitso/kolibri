#!/usr/bin/env bash
# Run the LSHE report for the previous month on this centre server.
#
# Runs on the host (not in the container), from the systemd timer
# lshe-report.timer on the 1st of each month at 02:00, or by hand:
#
#   sudo ./run_monthly_report.sh            # previous month
#   sudo ./run_monthly_report.sh 2027-03    # a given month (re-runs are safe)
#
# Writes lshe_<CENTRE_CODE>_<YYYY-MM>.csv (+ .json) into the container's
# LSHE_REPORT_DIR (host: /srv/lshe-reports) through
# the Kolibri container, and logs to $LSHE_LOG_DIR/report.log.

set -euo pipefail

CONTAINER="${LSHE_KOLIBRI_CONTAINER:-lshe-kolibri}"
LOG_DIR="${LSHE_LOG_DIR:-/var/log/lshe}"
LOG_FILE="${LOG_DIR}/report.log"
REPORT_TZ="${LSHE_REPORT_TIMEZONE:-Africa/Lusaka}"

mkdir -p "$LOG_DIR"

log() {
  printf '%s %s\n' "$(TZ="$REPORT_TZ" date '+%Y-%m-%dT%H:%M:%S%z')" "$*" | tee -a "$LOG_FILE"
}

if [[ $# -gt 1 ]]; then
  echo "usage: $0 [YYYY-MM]" >&2
  exit 2
fi

if [[ $# -eq 1 ]]; then
  MONTH="$1"
  if ! [[ "$MONTH" =~ ^[0-9]{4}-(0[1-9]|1[0-2])$ ]]; then
    echo "month must be YYYY-MM" >&2
    exit 2
  fi
else
  # Previous month in the report timezone: the 1st of this month minus one day.
  MONTH="$(TZ="$REPORT_TZ" date -d "$(TZ="$REPORT_TZ" date +%Y-%m-01) -1 day" +%Y-%m)"
fi

# Only one run at a time.
exec 9>"${LOG_DIR}/report.lock"
if ! flock -n 9; then
  log "another report run is in progress; exiting"
  exit 1
fi

if ! docker inspect -f '{{.State.Running}}' "$CONTAINER" 2>/dev/null | grep -q true; then
  log "ERROR container $CONTAINER is not running; report for $MONTH not written"
  exit 1
fi

# The output folder is the container's LSHE_REPORT_DIR (/srv/lshe-reports in
# docker-compose.yml), bind-mounted from the host; nothing to create here.
log "start lshereport --month $MONTH"
if docker exec "$CONTAINER" kolibri manage lshereport --month "$MONTH" \
    >>"$LOG_FILE" 2>&1; then
  log "done lshereport --month $MONTH"
else
  status=$?
  log "ERROR lshereport --month $MONTH failed (exit $status); see above"
  exit "$status"
fi
