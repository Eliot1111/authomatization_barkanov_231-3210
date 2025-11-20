"""
Тесты для моделей базы данных
"""
import pytest
from datetime import datetime
from models import (
    Publisher, Author, Branch, Faculty, Student,
    Book, BookAuthor, Inventory, BookFaculty, Borrow, User
)


class TestUserModel:
    """Тесты модели User"""
    
    def test_user_creation(self, test_session):
        """Тест: создание пользователя"""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password"
        )
        test_session.add(user)
        test_session.commit()
        
        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
    
    def test_user_flask_login_methods(self, test_session):
        """Тест: методы Flask-Login"""
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password"
        )
        
        assert user.is_authenticated() is True
        assert user.is_active() is True
        assert user.is_anonymous() is False
        assert user.get_id() is None  # До сохранения в БД


class TestBookModel:
    """Тесты модели Book"""
    
    def test_book_creation(self, test_session):
        """Тест: создание книги"""
        book = Book(
            title="Test Book",
            year=2020,
            pages=300,
            price=500.00
        )
        test_session.add(book)
        test_session.commit()
        
        assert book.id is not None
        assert book.title == "Test Book"
        assert book.year == 2020
    
    def test_book_with_publisher(self, test_session):
        """Тест: книга с издательством"""
        publisher = Publisher(name="Test Publisher")
        test_session.add(publisher)
        test_session.flush()
        
        book = Book(
            title="Test Book",
            publisher_id=publisher.id,
            year=2020
        )
        test_session.add(book)
        test_session.commit()
        
        assert book.publisher is not None
        assert book.publisher.name == "Test Publisher"


class TestBranchModel:
    """Тесты модели Branch"""
    
    def test_branch_creation(self, test_session):
        """Тест: создание филиала"""
        branch = Branch(
            name="Test Branch",
            address="Test Address 123"
        )
        test_session.add(branch)
        test_session.commit()
        
        assert branch.id is not None
        assert branch.name == "Test Branch"
        assert branch.address == "Test Address 123"


class TestBorrowModel:
    """Тесты модели Borrow"""
    
    def test_borrow_creation(self, test_session):
        """Тест: создание выдачи"""
        # Создаем необходимые данные
        faculty = Faculty(name="Test Faculty")
        book = Book(title="Test Book", year=2020)
        branch = Branch(name="Test Branch", address="Test Address")
        test_session.add_all([faculty, book, branch])
        test_session.flush()
        
        student = Student(full_name="Test Student", faculty_id=faculty.id)
        test_session.add(student)
        test_session.flush()
        
        borrow = Borrow(
            student_id=student.id,
            book_id=book.id,
            branch_id=branch.id,
            borrowed_at=datetime.utcnow()
        )
        test_session.add(borrow)
        test_session.commit()
        
        assert borrow.id is not None
        assert borrow.returned_at is None

