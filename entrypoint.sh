#!/bin/sh

set -e

if [ -n "$REDIS_URL" ]; then
    echo "Waiting for Redis to be ready..."
    until nc -z redis 6379; do
        sleep 1
    done
    echo "Redis is ready"
fi

if [ -n "$DATABASE_URL" ]; then
    # Wait for PostgreSQL to start
    echo "Waiting for PostgreSQL to start..."
    python << END
import socket
import time
import os
import psycopg2

host = "fileapp_db"
port = 5432
max_attempts = 30
attempt = 0

while attempt < max_attempts:
    try:
        with socket.create_connection((host, port), timeout=1):
            print(f"Successfully connected to {host}:{port}")
            break
    except socket.error as e:
        attempt += 1
        print(f"Attempt {attempt}/{max_attempts}: Cannot connect to {host}:{port}. Error: {e}")
        time.sleep(2)
else:
    print(f"Failed to connect to {host}:{port} after {max_attempts} attempts")
    exit(1)

print("Attempting to connect to the database...")
attempt = 0
while attempt < max_attempts:
    try:
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        print("Successfully connected to PostgreSQL")
        conn.close()
        break
    except psycopg2.OperationalError as e:
        attempt += 1
        print(f"Failed to connect to PostgreSQL (attempt {attempt}/{max_attempts}): {e}")
        time.sleep(2)
else:
    print("Failed to connect to PostgreSQL after maximum attempts")
    exit(1)

END
fi

# Run migrations
echo "Running migrations..."
python manage.py migrate
echo "Migrations complete"

# Start Celery worker
echo "Starting Celery worker..."
celery -A fileapp worker --pool=solo -l info &

# Start the configured web process
if [ "$#" -eq 0 ]; then
    set -- gunicorn fileapp.wsgi:application --bind 0.0.0.0:8000
fi

echo "Starting web process: $*"
exec "$@"
