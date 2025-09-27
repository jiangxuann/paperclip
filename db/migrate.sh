#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "DATABASE_URL not set. Usage: DATABASE_URL=postgres://user:pass@host:port/db ./db/migrate.sh" >&2
  exit 1
fi

MIG_DIR="$(dirname "$0")/migrations"

echo "Applying migrations in $MIG_DIR to $DATABASE_URL"

for file in $(ls -1 "$MIG_DIR"/*.sql | sort); do
  echo "Running: $(basename "$file")"
  psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$file"
done

echo "All migrations applied."
