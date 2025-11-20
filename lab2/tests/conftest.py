"""
Pytest configuration and fixtures for testing Flask application
"""
import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Используем тестовую БД (можно использовать SQLite для тестов)
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "sqlite:///test_library.db"  # Используем SQLite для простоты тестирования
)

@pytest.fixture(scope="session")
def test_engine():
    """Создает тестовый engine для БД"""
    engine = create_engine(TEST_DATABASE_URL, future=True, echo=False)
    yield engine
    engine.dispose()
    # Удаляем SQLite файл если используется
    if TEST_DATABASE_URL.startswith("sqlite"):
        try:
            os.remove("test_library.db")
        except:
            pass

@pytest.fixture(scope="function")
def test_session(test_engine):
    """Создает тестовую сессию для каждого теста"""
    from models import Base
    # Создаем все таблицы
    Base.metadata.create_all(test_engine)
    
    Session = sessionmaker(bind=test_engine)
    session = Session()
    
    yield session
    
    # Очищаем после теста
    session.rollback()
    session.close()
    # Очищаем таблицы
    Base.metadata.drop_all(test_engine)

@pytest.fixture
def app(test_engine):
    """Создает тестовое Flask приложение"""
    # Импортируем после создания engine, чтобы избежать циклических импортов
    import sys
    import importlib
    
    # Перезагружаем модуль app для использования тестовой БД
    if 'app' in sys.modules:
        importlib.reload(sys.modules['app'])
    
    from app import app as flask_app
    from app import SessionLocal
    
    # Создаем тестовую сессию
    TestSessionLocal = sessionmaker(bind=test_engine, autoflush=False, future=True)
    
    # Монkey-patch для использования тестовой БД
    import app as app_module
    original_session = app_module.SessionLocal
    app_module.SessionLocal = TestSessionLocal
    
    flask_app.config['TESTING'] = True
    flask_app.config['WTF_CSRF_ENABLED'] = False
    flask_app.config['SECRET_KEY'] = 'test-secret-key'
    
    yield flask_app
    
    # Восстанавливаем оригинальные значения
    app_module.SessionLocal = original_session

@pytest.fixture
def client(app):
    """Создает тестовый клиент Flask"""
    return app.test_client()

@pytest.fixture
def sample_user_data():
    """Возвращает тестовые данные пользователя"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123"
    }

@pytest.fixture
def sample_book_data():
    """Возвращает тестовые данные книги"""
    return {
        "title": "Test Book",
        "year": 2020,
        "pages": 300,
        "price": 500.00
    }

@pytest.fixture
def sample_branch_data():
    """Возвращает тестовые данные филиала"""
    return {
        "name": "Test Branch",
        "address": "Test Address 123"
    }

