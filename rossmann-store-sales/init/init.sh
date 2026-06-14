#!/usr/bin/env bash
set -euo pipefail

echo "Running DB init script..."
/opt/mssql-tools18/bin/sqlcmd \
  -S sqlserver \
  -U sa \
  -P "${MSSQL_SA_PASSWORD}" \
  -C \
  -b \
  -i /init/load_rossmann.sql

echo "Init completed."