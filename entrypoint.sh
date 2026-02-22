#!/bin/sh

echo "Waiting for Postgres..."

# Wait until Postgres is ready
until pg_isready -h postgres -p 5432 -U postgres
do
  sleep 2
done

echo "Postgres is ready. Running migrations..."

alembic upgrade head

echo "Starting API..."

exec uvicorn app.main:app --host 0.0.0.0 --port 8000