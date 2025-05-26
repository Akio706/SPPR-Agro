#!/bin/bash

# Устанавливаем фиксированные значения переменных
export POSTGRES_DB=frostdb
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=postgres

# Ждем, пока PostgreSQL будет готов к работе
until PGPASSWORD=$POSTGRES_PASSWORD psql -h "localhost" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c '\q'; do
  echo "Ожидание готовности PostgreSQL..."
  sleep 1
done

# Импортируем GPKG файл с помощью ogr2ogr
ogr2ogr -f "PostgreSQL" \
  PG:"host=localhost user=$POSTGRES_USER dbname=$POSTGRES_DB password=$POSTGRES_PASSWORD" \
  /docker-entrypoint-initdb.d/zones_regions.gpkg \
  -overwrite

echo "Импорт GPKG завершен" 