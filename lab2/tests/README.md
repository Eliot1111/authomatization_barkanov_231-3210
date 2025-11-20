# Тесты приложения

Набор тестов для библиотечного приложения, написанных на pytest.

## Структура тестов

- `conftest.py` - конфигурация pytest и фикстуры
- `test_auth.py` - тесты авторизации и регистрации
- `test_helpers.py` - тесты вспомогательных функций
- `test_routes.py` - тесты основных роутов
- `test_models.py` - тесты моделей базы данных

## Покрытие

Целевое покрытие кода: **40%**

Текущие тесты покрывают:
- ✅ Регистрация и авторизация пользователей
- ✅ Вспомогательные функции (available_copies, borrow_book, log_event)
- ✅ Основные роуты (index, books, branches, students)
- ✅ Модели базы данных (User, Book, Branch, Borrow)

## Запуск тестов

### Локально

```bash
cd lab2

# Активируйте виртуальное окружение
source venv/bin/activate

# Установите зависимости
pip install -r requirements-dev.txt

# Запустите все тесты
pytest tests/ -v

# Запустите с покрытием
pytest tests/ --cov=. --cov-report=html --cov-report=term

# Запустите конкретный файл тестов
pytest tests/test_auth.py -v

# Запустите конкретный тест
pytest tests/test_auth.py::TestRegistration::test_register_success -v
```

### В CI/CD

Тесты автоматически запускаются в GitHub Actions пайплайне:
1. Запуск всех тестов
2. Запуск с покрытием
3. Проверка покрытия (минимум 40%)
4. Загрузка отчетов о покрытии как артефакты

## Настройка тестовой БД

По умолчанию тесты используют SQLite (`test_library.db`), что не требует настройки PostgreSQL.

Для использования PostgreSQL в тестах установите переменную окружения:
```bash
export TEST_DATABASE_URL="postgresql+psycopg2://postgres:postgres@localhost:5432/test_library"
```

## Фикстуры

- `test_engine` - тестовый engine для БД
- `test_session` - тестовая сессия SQLAlchemy
- `app` - тестовое Flask приложение
- `client` - тестовый клиент Flask
- `sample_user_data` - тестовые данные пользователя
- `sample_book_data` - тестовые данные книги
- `sample_branch_data` - тестовые данные филиала

## Добавление новых тестов

1. Создайте новый файл `test_*.py` в папке `tests/`
2. Импортируйте необходимые фикстуры из `conftest.py`
3. Используйте префикс `Test*` для классов и `test_*` для функций
4. Запустите тесты и проверьте покрытие

## Пример теста

```python
def test_example(client, test_session):
    """Пример теста"""
    response = client.get('/')
    assert response.status_code == 200
```

