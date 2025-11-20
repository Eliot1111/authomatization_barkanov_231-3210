"""
Тесты для основных роутов приложения
"""
import pytest
from models import Book, Branch, Publisher, Faculty, Student


class TestIndexRoute:
    """Тесты главной страницы"""
    
    def test_index_page_loads(self, client):
        """Тест: главная страница загружается"""
        response = client.get('/')
        assert response.status_code == 200
    
    def test_index_shows_books_and_branches(self, client, test_session):
        """Тест: главная страница показывает книги и филиалы"""
        # Создаем тестовые данные
        book = Book(title="Test Book", year=2020)
        branch = Branch(name="Test Branch", address="Test Address")
        faculty = Faculty(name="Test Faculty")
        
        test_session.add_all([book, branch, faculty])
        test_session.commit()
        
        response = client.get('/')
        assert response.status_code == 200


class TestBooksRoutes:
    """Тесты роутов для книг"""
    
    def test_books_list_page_loads(self, client):
        """Тест: страница списка книг загружается"""
        response = client.get('/books')
        assert response.status_code == 200
    
    def test_books_list_shows_books(self, client, test_session):
        """Тест: список книг показывает книги"""
        # Создаем книгу
        publisher = Publisher(name="Test Publisher")
        test_session.add(publisher)
        test_session.flush()
        
        book = Book(title="Test Book", year=2020, publisher_id=publisher.id)
        test_session.add(book)
        test_session.commit()
        
        response = client.get('/books')
        assert response.status_code == 200
        assert b'Test Book' in response.data
    
    def test_book_add_page_loads(self, client):
        """Тест: страница добавления книги загружается"""
        response = client.get('/books/add')
        assert response.status_code == 200


class TestBranchesRoutes:
    """Тесты роутов для филиалов"""
    
    def test_branches_list_page_loads(self, client):
        """Тест: страница списка филиалов загружается"""
        response = client.get('/branches')
        assert response.status_code == 200
    
    def test_branches_list_shows_branches(self, client, test_session):
        """Тест: список филиалов показывает филиалы"""
        # Создаем филиал
        branch = Branch(name="Test Branch", address="Test Address")
        test_session.add(branch)
        test_session.commit()
        
        response = client.get('/branches')
        assert response.status_code == 200
        assert b'Test Branch' in response.data
    
    def test_branch_add_page_loads(self, client):
        """Тест: страница добавления филиала загружается"""
        response = client.get('/branches/add')
        assert response.status_code == 200


class TestStudentsRoute:
    """Тесты роута для студентов"""
    
    def test_students_page_loads(self, client):
        """Тест: страница студентов загружается"""
        response = client.get('/students')
        assert response.status_code == 200
    
    def test_students_shows_students(self, client, test_session):
        """Тест: страница показывает студентов"""
        # Создаем данные
        faculty = Faculty(name="Test Faculty")
        test_session.add(faculty)
        test_session.flush()
        
        student = Student(full_name="Test Student", faculty_id=faculty.id)
        test_session.add(student)
        test_session.commit()
        
        response = client.get('/students')
        assert response.status_code == 200
        assert b'Test Student' in response.data


class TestBorrowRoute:
    """Тесты роута для выдачи книг"""
    
    def test_borrow_page_loads(self, client):
        """Тест: страница выдачи загружается"""
        response = client.get('/borrow')
        assert response.status_code == 200


class TestEventsRoute:
    """Тесты роута для событий"""
    
    def test_events_page_loads(self, client):
        """Тест: страница событий загружается"""
        response = client.get('/events')
        assert response.status_code == 200

