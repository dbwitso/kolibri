#!/usr/bin/env bash
# Import the learner roster from MindSpark (read-only) into this centre's
# Kolibri.
#
#   ./run_import.sh [importer options]           # dry run only: shows counts
#   ./run_import.sh --apply [importer options]   # dry run, back up, then import
#
# Importer options are passed through to `kolibri manage importfrommindspark`,
# e.g. --org-id <ID>, --remove-inactive, --facility <ID>. See
# docs/lshe/roster-import.md for when to use each.
#
# With --apply, the Kolibri database is backed up (pg_dump, custom format) to
# $LSHE_BACKUP_DIR before anything is written. Logs go to $LSHE_LOG_DIR.

set -euo pipefail

KOLIBRI="${LSHE_KOLIBRI_CONTAINER:-lshe-kolibri}"
DB="${LSHE_DB_CONTAINER:-lshe-db}"
BACKUP_DIR="${LSHE_BACKUP_DIR:-/srv/lshe-backups}"
LOG_DIR="${LSHE_LOG_DIR:-/var/log/lshe}"
LOG_FILE="${LOG_DIR}/import.log"

APPLY=0
ARGS=()
for arg in "$@"; do
  case "$arg" in
    --apply) APPLY=1 ;;
    --dryrun) ;;  # always added for the first pass; ignore
    *) ARGS+=("$arg") ;;
  esac
done

mkdir -p "$LOG_DIR"
log() { printf '%s %s\n' "$(date '+%Y-%m-%dT%H:%M:%S%z')" "$*" | tee -a "$LOG_FILE"; }

for c in "$KOLIBRI" "$DB"; do
  if ! docker inspect -f '{{.State.Running}}' "$c" 2>/dev/null | grep -q true; then
    log "ERROR container $c is not running"
    exit 1
  fi
done

manage() { docker exec "$KOLIBRI" kolibri manage importfrommindspark "$@"; }

log "dry run: importfrommindspark --dryrun ${ARGS[*]:-}"
if ! manage --dryrun ${ARGS[@]+"${ARGS[@]}"} 2>&1 | tee -a "$LOG_FILE"; then
  log "ERROR dry run failed; nothing was changed"
  exit 1
fi

if [[ $APPLY -ne 1 ]]; then
  log "dry run only: nothing was changed. Re-run with --apply to import."
  exit 0
fi

# Back up first. Database credentials come from the db container's own env.
mkdir -p "$BACKUP_DIR"
chmod 700 "$BACKUP_DIR"
BACKUP="${BACKUP_DIR}/kolibri_$(date +%Y%m%d_%H%M%S)_before_import.dump"
log "backing up the Kolibri database to $BACKUP"
if ! docker exec "$DB" sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' >"$BACKUP"; then
  log "ERROR backup failed; import not run"
  rm -f "$BACKUP"
  exit 1
fi
# A dump that pg_restore cannot list is not a backup.
if ! docker exec -i "$DB" pg_restore --list >/dev/null <"$BACKUP"; then
  log "ERROR backup $BACKUP is not readable; import not run"
  exit 1
fi
chmod 600 "$BACKUP"
log "backup ok ($(du -h "$BACKUP" | cut -f1))"

log "import: importfrommindspark ${ARGS[*]:-}"
if manage ${ARGS[@]+"${ARGS[@]}"} 2>&1 | tee -a "$LOG_FILE"; then
  log "import done. To undo it, restore $BACKUP (see docs/lshe/deployment.md, Restore)."
else
  log "ERROR import failed; it runs in one transaction, so nothing was written. Backup: $BACKUP"
  exit 1
fi
