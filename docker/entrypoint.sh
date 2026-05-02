#!/usr/bin/env sh
set -e

MAX_MIGRATION_ATTEMPTS="${MAX_MIGRATION_ATTEMPTS:-30}"
MIGRATION_RETRY_SECONDS="${MIGRATION_RETRY_SECONDS:-2}"
attempt=1

while [ "$attempt" -le "$MAX_MIGRATION_ATTEMPTS" ]; do
  if alembic upgrade head; then
    break
  fi

  if [ "$attempt" -eq "$MAX_MIGRATION_ATTEMPTS" ]; then
    echo "Database migrations failed after $MAX_MIGRATION_ATTEMPTS attempts" >&2
    exit 1
  fi

  echo "Database is not ready for migrations, retrying in ${MIGRATION_RETRY_SECONDS}s (${attempt}/${MAX_MIGRATION_ATTEMPTS})" >&2
  attempt=$((attempt + 1))
  sleep "$MIGRATION_RETRY_SECONDS"
done

exec uvicorn src.main:app --host 0.0.0.0 --port 8000
