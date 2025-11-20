#!/bin/bash
# Скрипт для применения миграций с сохранением старой схемы

set -e

echo "=== Database Migration Process ==="

# Переходим в директорию проекта
cd "$(dirname "$0")/.." || exit 1

# Проверяем наличие Alembic
if ! command -v alembic &> /dev/null; then
    echo "ERROR: Alembic not found. Installing..."
    pip install alembic
fi

# Создаем бэкап старой схемы
echo "Step 1: Creating backup of current schema..."
if [ -f "migrations/backup_schema.sh" ]; then
    chmod +x migrations/backup_schema.sh
    ./migrations/backup_schema.sh
else
    echo "WARNING: backup_schema.sh not found, skipping backup"
fi

# Проверяем текущую версию
echo ""
echo "Step 2: Checking current migration version..."
alembic current || echo "No migrations applied yet"

# Применяем миграции
echo ""
echo "Step 3: Applying migrations..."
alembic upgrade head

if [ $? -eq 0 ]; then
    echo "✓ Migrations applied successfully"
else
    echo "✗ ERROR: Failed to apply migrations"
    exit 1
fi

# Показываем новую версию
echo ""
echo "Step 4: Current migration version:"
alembic current

echo ""
echo "=== Migration Process Completed ==="

