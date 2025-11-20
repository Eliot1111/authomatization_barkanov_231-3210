#!/bin/bash
# Скрипт для сохранения старой схемы БД перед применением миграций

# Получаем параметры
DB_URL="${DATABASE_URL:-postgresql+psycopg2://postgres:postgres@localhost:5432/postgres}"
BACKUP_DIR="${SCHEMA_BACKUP_DIR:-/var/backups/db_schemas}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
SCHEMA_NAME="lib"

# Создаем директорию для бэкапов, если её нет
mkdir -p "$BACKUP_DIR"

# Извлекаем параметры подключения из DATABASE_URL
# Формат: postgresql+psycopg2://user:password@host:port/database
DB_USER=$(echo "$DB_URL" | sed -n 's|.*://\([^:]*\):.*|\1|p')
DB_PASS=$(echo "$DB_URL" | sed -n 's|.*://[^:]*:\([^@]*\)@.*|\1|p')
DB_HOST=$(echo "$DB_URL" | sed -n 's|.*@\([^:]*\):.*|\1|p')
DB_PORT=$(echo "$DB_URL" | sed -n 's|.*:\([0-9]*\)/.*|\1|p')
DB_NAME=$(echo "$DB_URL" | sed -n 's|.*/\([^?]*\).*|\1|p')

# Имя файла бэкапа
BACKUP_FILE="${BACKUP_DIR}/schema_${SCHEMA_NAME}_${TIMESTAMP}.sql"

echo "Backing up schema ${SCHEMA_NAME} to ${BACKUP_FILE}..."

# Экспортируем схему БД
PGPASSWORD="$DB_PASS" pg_dump \
    -h "$DB_HOST" \
    -p "${DB_PORT:-5432}" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    --schema="$SCHEMA_NAME" \
    --schema-only \
    --no-owner \
    --no-privileges \
    > "$BACKUP_FILE" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✓ Schema backup created: ${BACKUP_FILE}"
    # Создаем симлинк на последний бэкап
    ln -sf "$BACKUP_FILE" "${BACKUP_DIR}/schema_${SCHEMA_NAME}_latest.sql"
    echo "✓ Latest backup link created"
else
    echo "✗ ERROR: Failed to create schema backup"
    exit 1
fi

# Также сохраняем список таблиц
TABLES_FILE="${BACKUP_DIR}/tables_${SCHEMA_NAME}_${TIMESTAMP}.txt"
PGPASSWORD="$DB_PASS" psql \
    -h "$DB_HOST" \
    -p "${DB_PORT:-5432}" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    -t -c "SELECT tablename FROM pg_tables WHERE schemaname='${SCHEMA_NAME}';" \
    > "$TABLES_FILE" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✓ Tables list saved: ${TABLES_FILE}"
fi

echo "Backup completed successfully"

