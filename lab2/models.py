# models.py
from __future__ import annotations
from datetime import datetime
from typing import List

from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, Numeric, DateTime, ForeignKey,
    UniqueConstraint, CheckConstraint, MetaData
)
from sqlalchemy.orm import declarative_base, relationship

# Все таблицы в схеме lib
metadata = MetaData(schema="lib")
Base = declarative_base(metadata=metadata)

class Publisher(Base):
    __tablename__ = "publishers"
    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True, nullable=False)

    books = relationship("Book", back_populates="publisher")

class Author(Base):
    __tablename__ = "authors"
    id = Column(Integer, primary_key=True)
    full_name = Column(Text, nullable=False)

    books = relationship("BookAuthor", back_populates="author")

class Branch(Base):
    __tablename__ = "branches"
    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True, nullable=False)
    address = Column(Text)

    inventories = relationship("Inventory", back_populates="branch")
    book_faculties = relationship("BookFaculty", back_populates="branch")
    borrows = relationship("Borrow", back_populates="branch")

class Faculty(Base):
    __tablename__ = "faculties"
    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True, nullable=False)

    students = relationship("Student", back_populates="faculty")
    book_faculties = relationship("BookFaculty", back_populates="faculty")

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True)
    full_name = Column(Text, nullable=False)
    faculty_id = Column(Integer, ForeignKey("lib.faculties.id"), nullable=False)

    faculty = relationship("Faculty", back_populates="students")
    borrows = relationship("Borrow", back_populates="student")

class Book(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True)
    title = Column(Text, nullable=False)
    publisher_id = Column(Integer, ForeignKey("lib.publishers.id"))
    year = Column(Integer)
    pages = Column(Integer)
    illustrations = Column(Integer, default=0)
    price = Column(Numeric(10, 2))

    __table_args__ = (
        CheckConstraint("year BETWEEN 1500 AND 2100", name="ck_books_year"),
        CheckConstraint("pages >= 1", name="ck_books_pages"),
        CheckConstraint("illustrations >= 0", name="ck_books_illustrations"),
        CheckConstraint("price >= 0", name="ck_books_price"),
    )

    publisher = relationship("Publisher", back_populates="books")
    authors = relationship("BookAuthor", back_populates="book", cascade="all, delete-orphan")
    inventories = relationship("Inventory", back_populates="book")
    book_faculties = relationship("BookFaculty", back_populates="book")
    borrows = relationship("Borrow", back_populates="book")

class BookAuthor(Base):
    __tablename__ = "book_authors"
    book_id = Column(Integer, ForeignKey("lib.books.id", ondelete="CASCADE"), primary_key=True)
    author_id = Column(Integer, ForeignKey("lib.authors.id", ondelete="CASCADE"), primary_key=True)

    book = relationship("Book", back_populates="authors")
    author = relationship("Author", back_populates="books")

class Inventory(Base):
    __tablename__ = "inventories"
    id = Column(Integer, primary_key=True)
    book_id = Column(Integer, ForeignKey("lib.books.id", ondelete="CASCADE"), nullable=False)
    branch_id = Column(Integer, ForeignKey("lib.branches.id", ondelete="CASCADE"), nullable=False)
    copies_total = Column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint("book_id", "branch_id", name="uq_inventories_book_branch"),
        CheckConstraint("copies_total >= 0", name="ck_inventories_nonneg"),
    )

    book = relationship("Book", back_populates="inventories")
    branch = relationship("Branch", back_populates="inventories")

class BookFaculty(Base):
    __tablename__ = "book_faculties"
    book_id = Column(Integer, ForeignKey("lib.books.id", ondelete="CASCADE"), primary_key=True)
    faculty_id = Column(Integer, ForeignKey("lib.faculties.id", ondelete="CASCADE"), primary_key=True)
    branch_id = Column(Integer, ForeignKey("lib.branches.id", ondelete="CASCADE"), primary_key=True)

    book = relationship("Book", back_populates="book_faculties")
    faculty = relationship("Faculty", back_populates="book_faculties")
    branch = relationship("Branch", back_populates="book_faculties")

class Borrow(Base):
    __tablename__ = "borrows"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("lib.students.id", ondelete="CASCADE"), nullable=False)
    book_id = Column(Integer, ForeignKey("lib.books.id", ondelete="CASCADE"), nullable=False)
    branch_id = Column(Integer, ForeignKey("lib.branches.id", ondelete="CASCADE"), nullable=False)
    borrowed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    returned_at = Column(DateTime)

    student = relationship("Student", back_populates="borrows")
    book = relationship("Book", back_populates="borrows")
    branch = relationship("Branch", back_populates="borrows")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(Text, unique=True, nullable=False)
    email = Column(Text, unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Методы для Flask-Login
    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

class EventLog(Base):
    __tablename__ = "event_log"
    id = Column(BigInteger, primary_key=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    event = Column(Text, nullable=False)
    details = Column(Text)  # храним JSON как текст для простоты; можно поменять на JSONB через Dialect
