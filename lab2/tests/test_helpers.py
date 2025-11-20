"""
Тесты для вспомогательных функций
"""
import pytest
from datetime import datetime
from models import Book, Branch, Inventory, Borrow, Student, EventLog
from app import available_copies, borrow_book, BorrowError, log_event


class TestAvailableCopies:
    """Тесты функции available_copies"""
    
    def test_available_copies_no_inventory(self, test_session):
        """Тест: нет инвентаря - возвращает 0"""
        result = available_copies(test_session, book_id=1, branch_id=1)
        assert result == 0
    
    def test_available_copies_with_inventory(self, test_session):
        """Тест: есть инвентарь без выданных книг"""
        # Создаем книгу и филиал
        book = Book(title="Test Book", year=2020)
        branch = Branch(name="Test Branch", address="Test Address")
        test_session.add(book)
        test_session.add(branch)
        test_session.flush()
        
        # Создаем инвентарь
        inventory = Inventory(
            book_id=book.id,
            branch_id=branch.id,
            copies_total=5
        )
        test_session.add(inventory)
        test_session.commit()
        
        result = available_copies(test_session, book_id=book.id, branch_id=branch.id)
        assert result == 5
    
    def test_available_copies_with_borrows(self, test_session):
        """Тест: есть инвентарь с выданными книгами"""
        # Создаем данные
        book = Book(title="Test Book", year=2020)
        branch = Branch(name="Test Branch", address="Test Address")
        faculty = Faculty(name="Test Faculty")
        test_session.add_all([book, branch, faculty])
        test_session.flush()
        
        student = Student(full_name="Test Student", faculty_id=faculty.id)
        test_session.add(student)
        test_session.flush()
        
        # Создаем инвентарь
        inventory = Inventory(
            book_id=book.id,
            branch_id=branch.id,
            copies_total=5
        )
        test_session.add(inventory)
        
        # Создаем выдачу
        borrow = Borrow(
            student_id=student.id,
            book_id=book.id,
            branch_id=branch.id,
            borrowed_at=datetime.utcnow()
        )
        test_session.add(borrow)
        test_session.commit()
        
        result = available_copies(test_session, book_id=book.id, branch_id=branch.id)
        assert result == 4  # 5 - 1 = 4


class TestBorrowBook:
    """Тесты функции borrow_book"""
    
    def test_borrow_book_success(self, test_session):
        """Тест: успешная выдача книги"""
        # Создаем данные
        book = Book(title="Test Book", year=2020)
        branch = Branch(name="Test Branch", address="Test Address")
        faculty = Faculty(name="Test Faculty")
        test_session.add_all([book, branch, faculty])
        test_session.flush()
        
        student = Student(full_name="Test Student", faculty_id=faculty.id)
        test_session.add(student)
        test_session.flush()
        
        # Создаем инвентарь
        inventory = Inventory(
            book_id=book.id,
            branch_id=branch.id,
            copies_total=5
        )
        test_session.add(inventory)
        test_session.commit()
        
        # Выдаем книгу
        borrow_book(test_session, student.id, book.id, branch.id)
        test_session.commit()
        
        # Проверяем, что выдача создана
        borrow = test_session.query(Borrow).filter_by(
            student_id=student.id,
            book_id=book.id,
            branch_id=branch.id,
            returned_at=None
        ).first()
        assert borrow is not None
    
    def test_borrow_book_no_copies(self, test_session):
        """Тест: выдача при отсутствии доступных экземпляров"""
        # Создаем данные
        book = Book(title="Test Book", year=2020)
        branch = Branch(name="Test Branch", address="Test Address")
        faculty = Faculty(name="Test Faculty")
        test_session.add_all([book, branch, faculty])
        test_session.flush()
        
        student = Student(full_name="Test Student", faculty_id=faculty.id)
        test_session.add(student)
        test_session.flush()
        
        # НЕ создаем инвентарь (0 экземпляров)
        test_session.commit()
        
        # Пытаемся выдать книгу
        with pytest.raises(BorrowError, match="Нет доступных экземпляров"):
            borrow_book(test_session, student.id, book.id, branch.id)


class TestLogEvent:
    """Тесты функции log_event"""
    
    def test_log_event_creates_record(self, test_session):
        """Тест: создание записи в логе событий"""
        log_event(test_session, "TEST_EVENT", '{"test": "data"}')
        test_session.commit()
        
        event = test_session.query(EventLog).filter_by(event="TEST_EVENT").first()
        assert event is not None
        assert event.details == '{"test": "data"}'
    
    def test_log_event_without_details(self, test_session):
        """Тест: создание записи без деталей"""
        log_event(test_session, "SIMPLE_EVENT")
        test_session.commit()
        
        event = test_session.query(EventLog).filter_by(event="SIMPLE_EVENT").first()
        assert event is not None
        assert event.details is None

