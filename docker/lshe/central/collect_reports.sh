#!/usr/bin/env bash
# Pull LSHE report files from every centre over NetBird, with rsync over SSH
# as the read-only `lshe-reports` user. Runs on the central machine.
#
#   ./collect_reports.sh [-c centres.conf] [-o collected_dir]
#
# Each centre's files land in <collected_dir>/<CENTRE_CODE>/. A centre that
# cannot be reached is logged and skipped; the others still run. The exit
# status is 1 if any centre failed, so a timer or cron job can alert on it.
#
# Settings (environment):
#   LSHE_SSH_KEY          private key for the lshe-reports user
#                         (default ~/.ssh/lshe_reports)
#   LSHE_REMOTE_PATH      path on the centre (default "./", which is
#                         /srv/lshe-reports when the key is restricted with
#                         `rrsync -ro /srv/lshe-reports`, as README.md sets up)
#   LSHE_COLLECT_LOG      log file (default <collected_dir>/collect.log)

set -uo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
CONF="$HERE/centres.conf"
OUT="$HERE/collected"
while getopts "c:o:" opt; do
  case "$opt" in
    c) CONF="$OPTARG" ;;
    o) OUT="$OPTARG" ;;
    *) echo "usage: $0 [-c centres.conf] [-o collected_dir]" >&2; exit 2 ;;
  esac
done

KEY="${LSHE_SSH_KEY:-$HOME/.ssh/lshe_reports}"
REMOTE_PATH="${LSHE_REMOTE_PATH:-./}"
mkdir -p "$OUT"
LOG="${LSHE_COLLECT_LOG:-$OUT/collect.log}"

log() { printf '%s %s\n' "$(date '+%Y-%m-%dT%H:%M:%S%z')" "$*" | tee -a "$LOG"; }

if [[ ! -r "$CONF" ]]; then
  echo "centres file not found: $CONF (copy centres.conf.example)" >&2
  exit 2
fi
if [[ ! -r "$KEY" ]]; then
  echo "SSH key not found: $KEY (set LSHE_SSH_KEY)" >&2
  exit 2
fi

ok=0
failed=()
while read -r code host port user _rest; do
  [[ -z "${code:-}" || "$code" == \#* ]] && continue
  if ! [[ "$code" =~ ^[A-Za-z0-9_-]{1,32}$ ]]; then
    log "skip bad centre code '$code'"
    failed+=("$code")
    continue
  fi
  port="${port:-22}"
  user="${user:-lshe-reports}"
  dest="$OUT/$code/"
  mkdir -p "$dest"
  log "collect $code from $user@$host:$port"
  # stdin is /dev/null so ssh does not swallow the rest of $CONF.
  # Only this centre's report files; nothing is deleted locally, so a
  # centre that has lost files does not erase the central copy.
  if rsync -a --timeout=60 \
      -e "ssh -i $KEY -p $port -o BatchMode=yes -o ConnectTimeout=20 -o StrictHostKeyChecking=yes" \
      --include="lshe_${code}_*.csv" --include="lshe_${code}_*.json" --exclude='*' \
      "$user@$host:$REMOTE_PATH" "$dest" </dev/null >>"$LOG" 2>&1; then
    ok=$((ok + 1))
    log "ok $code ($(find "$dest" -name 'lshe_*.csv' | wc -l) report file(s))"
  else
    log "FAILED $code (unreachable or refused); see log"
    failed+=("$code")
  fi
done <"$CONF"

log "collected from $ok centre(s); failed: ${failed[*]:-none}"
[[ ${#failed[@]} -eq 0 ]]
