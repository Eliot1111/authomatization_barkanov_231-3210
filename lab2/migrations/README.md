# Database Migrations

Этот каталог содержит скрипты для управления миграциями базы данных.

## Структура

- `backup_schema.sh` - скрипт для создания бэкапа схемы БД перед применением миграций
- `apply_migrations.sh` - скрипт для применения миграций с автоматическим бэкапом
- `backups/` - директория для хранения бэкапов схем (создается автоматически)

## Использование

### Создание бэкапа схемы

```bash
cd lab2
export DATABASE_URL="postgresql+psycopg2://postgres:postgres@localhost:5432/postgres"
export SCHEMA_BACKUP_DIR="/var/backups/db_schemas"  # опционально
./migrations/backup_schema.sh
```

### Применение миграций

```bash
cd lab2
./migrations/apply_migrations.sh
```

Или вручную:

```bash
cd lab2
source venv/bin/activate
alembic upgrade head
```

## Создание новой миграции

```bash
cd lab2
source venv/bin/activate

# Автоматическое создание миграции на основе изменений в models.py
alembic revision --autogenerate -m "Описание изменений"

# Ручное создание миграции
alembic revision -m "Описание изменений"
```

## Просмотр истории миграций

```bash
alembic history
alembic current
```

## Откат миграций

```bash
# Откат на одну версию назад
alembic downgrade -1

# Откат до конкретной версии
alembic downgrade <revision_id>

# Откат всех миграций
alembic downgrade base
```

## Бэкапы

Бэкапы схем сохраняются в директории, указанной в переменной окружения `SCHEMA_BACKUP_DIR` (по умолчанию `/var/backups/db_schemas`).

Формат имени файла: `schema_lib_YYYYMMDD_HHMMSS.sql`

Также создается симлинк `schema_lib_latest.sql` на последний бэкап.

## В CI/CD

Миграции автоматически применяются в GitHub Actions пайплайне:
1. Создается бэкап текущей схемы
2. Проверяется наличие новых миграций
3. Применяются все миграции
4. Проверяется, что новые таблицы созданы

