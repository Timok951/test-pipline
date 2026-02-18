#!/bin/bash
set -euo pipefail

# ────────────────────────────────────────────────
# Ждём, пока PostgreSQL реально готов принимать запросы
# Используем pg_isready (если есть) или улучшенный psycopg2-цикл

echo "Waiting for PostgreSQL..."

until python - <<EOF
import os, time, sys
import psycopg2
from psycopg2 import OperationalError

host     = os.getenv("DATABASE_HOST",     "postgres_db")
port     = int(os.getenv("DATABASE_PORT",     "5432"))
user     = os.getenv("DATABASE_USERNAME", "postgres")
password = os.getenv("DATABASE_PASSWORD", "1")
dbname   = os.getenv("DATABASE_NAME",     "ShopBoom")

attempts = 0
max_attempts = 30

while attempts < max_attempts:
    try:
        conn = psycopg2.connect(
            host=host, port=port, user=user,
            password=password, dbname=dbname,
            connect_timeout=2
        )
        conn.close()
        print("PostgreSQL is accepting connections", file=sys.stderr)
        sys.exit(0)
    except OperationalError as e:
        attempts += 1
        print(f"Attempt {attempts}/{max_attempts}: {e}", file=sys.stderr)
        time.sleep(2)

print("PostgreSQL did not become ready in time", file=sys.stderr)
sys.exit(1)
EOF
do
    sleep 1
done

echo "PostgreSQL is ready!"

# ────────────────────────────────────────────────
# Миграции (лучше по приложениям, если есть зависимость)
python manage.py migrate --noinput

# Если есть кастомные начальные данные или view — можно отдельно
# python manage.py migrate analytics --noinput

# Суперпользователь (твой код нормальный, но чуть чище)
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='$DJANGO_SUPERUSER_USERNAME').exists():
    User.objects.create_superuser(
        '$DJANGO_SUPERUSER_USERNAME',
        '$DJANGO_SUPERUSER_EMAIL',
        '$DJANGO_SUPERUSER_PASSWORD'
    )
"

# Запуск
exec python manage.py runserver 0.0.0.0:8000