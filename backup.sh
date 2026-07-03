#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
DB_FILE="${PROJECT_DIR}/db.sqlite3"
BACKUP_DIR="${PROJECT_DIR}/backups"
RETENTION_DAYS=7

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"
}

if [ ! -f "$DB_FILE" ]; then
    log "ERROR: Database file not found at ${DB_FILE}"
    exit 1
fi

mkdir -p "$BACKUP_DIR"

BACKUP_FILE="${BACKUP_DIR}/backup-$(date '+%Y-%m-%d').sqlite3"

log "Starting backup to ${BACKUP_FILE}..."
sqlite3 "$DB_FILE" ".backup '${BACKUP_FILE}'"

if [ -f "$BACKUP_FILE" ]; then
    log "Backup completed successfully (${BACKUP_FILE})"
else
    log "ERROR: Backup file was not created"
    exit 1
fi

log "Pruning backups older than ${RETENTION_DAYS} days..."
find "$BACKUP_DIR" -name "backup-*.sqlite3" -mtime +"$RETENTION_DAYS" -delete 2>/dev/null || true

log "Done."
