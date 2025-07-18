#!/bin/bash
set -e

# DATABASES is a list of database names to create if they do not exist, separated by commas
IFS=',' read -r -a DATABASES <<< ${DATABASES:-"entity-store,ndsdb,customizer,evaluation"}
echo "Creating additional databases: ${DATABASES[*]}"

until PGPASSWORD=$POSTGRESQL_PASSWORD psql -h localhost -U $POSTGRESQL_USERNAME -d $POSTGRESQL_DATABASE -c '\q'; do
  echo "PostgreSQL is unavailable - sleeping"
  sleep 1
done

echo "PostgreSQL is up - creating NeMo microservices databases"

# Create each database if it doesn't exist
for db in "${DATABASES[@]}"; do
  if ! PGPASSWORD=$POSTGRESQL_PASSWORD psql -h localhost -U $POSTGRESQL_USERNAME -lqt | cut -d \| -f 1 | grep -qw $db; then
    echo "Creating database: $db"
    PGPASSWORD=$POSTGRESQL_PASSWORD psql -v ON_ERROR_STOP=1 -h localhost -U $POSTGRESQL_USERNAME -d $POSTGRESQL_DATABASE <<-EOSQL
      CREATE DATABASE "$db";
      GRANT ALL PRIVILEGES ON DATABASE "$db" TO $POSTGRESQL_USERNAME;
EOSQL
    echo "Database $db created successfully."
  else
    echo "Database $db already exists. Skipping creation."
  fi
done

echo "Additional databases created successfully: ${DATABASES[*]}"
