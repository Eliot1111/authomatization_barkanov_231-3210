"""
Тесты для функционала авторизации и регистрации
"""
import pytest
from flask import url_for
from werkzeug.security import check_password_hash
from models import User


class TestRegistration:
    """Тесты регистрации пользователей"""
    
    def test_register_page_loads(self, client):
        """Тест: страница регистрации загружается"""
        response = client.get('/register')
        assert response.status_code == 200
        assert b'Регистрация' in response.data or b'register' in response.data.lower()
    
    def test_register_success(self, client, test_session, sample_user_data):
        """Тест: успешная регистрация пользователя"""
        response = client.post('/register', data={
            'username': sample_user_data['username'],
            'email': sample_user_data['email'],
            'password': sample_user_data['password'],
            'password_confirm': sample_user_data['password']
        }, follow_redirects=True)
        
        # Проверяем, что пользователь создан
        user = test_session.query(User).filter_by(username=sample_user_data['username']).first()
        assert user is not None
        assert user.email == sample_user_data['email']
        assert check_password_hash(user.password_hash, sample_user_data['password'])
    
    def test_register_empty_fields(self, client):
        """Тест: регистрация с пустыми полями"""
        response = client.post('/register', data={
            'username': '',
            'email': '',
            'password': '',
            'password_confirm': ''
        })
        assert response.status_code == 200
        assert b'обязательны' in response.data.lower() or b'required' in response.data.lower()
    
    def test_register_password_mismatch(self, client):
        """Тест: регистрация с несовпадающими паролями"""
        response = client.post('/register', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123',
            'password_confirm': 'password456'
        })
        assert response.status_code == 200
        assert b'совпадают' in response.data.lower() or b'match' in response.data.lower()
    
    def test_register_short_password(self, client):
        """Тест: регистрация с коротким паролем"""
        response = client.post('/register', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': '12345',
            'password_confirm': '12345'
        })
        assert response.status_code == 200
        assert b'6' in response.data or b'символов' in response.data.lower()


class TestLogin:
    """Тесты входа в систему"""
    
    def test_login_page_loads(self, client):
        """Тест: страница входа загружается"""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'Вход' in response.data or b'login' in response.data.lower()
    
    def test_login_success(self, client, test_session, sample_user_data):
        """Тест: успешный вход"""
        from werkzeug.security import generate_password_hash
        
        # Создаем пользователя
        user = User(
            username=sample_user_data['username'],
            email=sample_user_data['email'],
            password_hash=generate_password_hash(sample_user_data['password'])
        )
        test_session.add(user)
        test_session.commit()
        
        response = client.post('/login', data={
            'username': sample_user_data['username'],
            'password': sample_user_data['password']
        }, follow_redirects=True)
        
        # Проверяем редирект на главную
        assert response.status_code == 200
    
    def test_login_invalid_credentials(self, client):
        """Тест: вход с неверными данными"""
        response = client.post('/login', data={
            'username': 'nonexistent',
            'password': 'wrongpassword'
        })
        assert response.status_code == 200
        assert b'неверное' in response.data.lower() or b'invalid' in response.data.lower() or b'wrong' in response.data.lower()
    
    def test_login_empty_fields(self, client):
        """Тест: вход с пустыми полями"""
        response = client.post('/login', data={
            'username': '',
            'password': ''
        })
        assert response.status_code == 200


class TestLogout:
    """Тесты выхода из системы"""
    
    def test_logout_requires_login(self, client):
        """Тест: выход требует авторизации"""
        response = client.get('/logout', follow_redirects=True)
        # Должен быть редирект на страницу входа
        assert response.status_code == 200

