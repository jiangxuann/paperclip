#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${DATABASE_URL:-}" ]];n+then
  echo "DATABASE_URL not set. Usage: DATABASE_URL=postgres://user:pass@host:port/db ./db/migrate.sh" >&2
  exit 1
fi

echo "Applying migrations to $DATABASE_URL"
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$(dirname "$0")/migrations/0001_init.sql"
echo "Done."

