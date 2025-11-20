# app.py
import os
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import sessionmaker

from models import (
    Base, Publisher, Author, Branch, Faculty, Student,
    Book, BookAuthor, Inventory, BookFaculty, Borrow, EventLog, User
)
from db_bootstrap import init_db

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@localhost:5432/postgres")
SECRET_KEY = os.getenv("FLASK_SECRET", "dev-secret")

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, future=True)

# Инициализация БД (ORM-таблицы + представление/триггер + демо-данные)
init_db(engine, with_demo=True)

app = Flask(__name__)
app.secret_key = SECRET_KEY

# Настройка Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Пожалуйста, войдите в систему для доступа к этой странице.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    with SessionLocal() as session:
        return session.get(User, int(user_id))


# ---------- Вспомогательные функции уровня сервиса ----------

def log_event(session, event: str, details: str | None = None):
    session.add(EventLog(event=event, details=details))

def available_copies(session, book_id: int, branch_id: int) -> int:
    inv = session.query(Inventory).filter_by(book_id=book_id, branch_id=branch_id).one_or_none()
    total = inv.copies_total if inv else 0
    active = session.query(func.count(Borrow.id)).filter(
        Borrow.book_id == book_id,
        Borrow.branch_id == branch_id,
        Borrow.returned_at.is_(None),
    ).scalar() or 0
    return total - active

class BorrowError(Exception):
    pass

def borrow_book(session, student_id: int, book_id: int, branch_id: int):
    avail = available_copies(session, book_id, branch_id)
    if avail <= 0:
        log_event(session, "NO_COPIES_AVAILABLE",
                  details=f'{{"student_id":{student_id},"book_id":{book_id},"branch_id":{branch_id}}}')
        raise BorrowError("Нет доступных экземпляров для выдачи.")
    session.add(Borrow(student_id=student_id, book_id=book_id, branch_id=branch_id))


# ---------------------------- Роуты ----------------------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")

        if not username or not email or not password:
            flash("Все поля обязательны для заполнения", "danger")
            return render_template("register.html")

        if password != password_confirm:
            flash("Пароли не совпадают", "danger")
            return render_template("register.html")

        if len(password) < 6:
            flash("Пароль должен содержать не менее 6 символов", "danger")
            return render_template("register.html")

        with SessionLocal() as session:
            # Проверка на существующего пользователя
            existing_user = session.query(User).filter(
                (User.username == username) | (User.email == email)
            ).first()
            if existing_user:
                flash("Пользователь с таким именем или email уже существует", "danger")
                return render_template("register.html")

            # Создание нового пользователя
            password_hash = generate_password_hash(password)
            new_user = User(
                username=username,
                email=email,
                password_hash=password_hash
            )
            session.add(new_user)
            session.commit()
            flash("Регистрация успешна! Теперь вы можете войти.", "success")
            return redirect(url_for("login"))

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Введите имя пользователя и пароль", "danger")
            return render_template("login.html")

        with SessionLocal() as session:
            user = session.query(User).filter_by(username=username).first()
            if user and check_password_hash(user.password_hash, password):
                login_user(user)
                flash(f"Добро пожаловать, {user.username}!", "success")
                next_page = request.args.get("next")
                return redirect(next_page or url_for("index"))
            else:
                flash("Неверное имя пользователя или пароль", "danger")

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Вы вышли из системы", "info")
    return redirect(url_for("index"))

@app.route("/")
def index():
    with SessionLocal() as session:
        books = session.query(Book.id, Book.title).order_by(Book.title).all()
        branches = session.query(Branch.id, Branch.name).order_by(Branch.name).all()
        faculties = session.query(Faculty.id, Faculty.name).order_by(Faculty.name).all()
    return render_template("index.html", books=books, branches=branches, faculties=faculties)

# 1) Количество экземпляров указанной книги в филиале
@app.route("/branches/<int:branch_id>/books/<int:book_id>/copies")
def copies_in_branch(branch_id, book_id):
    with SessionLocal() as session:
        total = session.query(Inventory.copies_total).filter_by(
            book_id=book_id, branch_id=branch_id
        ).scalar() or 0
        avail = available_copies(session, book_id, branch_id)
        title = session.query(Book.title).filter_by(id=book_id).scalar()
        bname = session.query(Branch.name).filter_by(id=branch_id).scalar()
    return render_template("copies.html", title=title, branch=bname, total=total, available=avail)

# 2) Факультеты, где книга используется в филиале
@app.route("/branches/<int:branch_id>/books/<int:book_id>/faculties")
def book_faculties(branch_id, book_id):
    with SessionLocal() as session:
        count = session.query(func.count("*")).select_from(BookFaculty).filter_by(
            book_id=book_id, branch_id=branch_id
        ).scalar()
        names = [
            n for (n,) in session.query(Faculty.name)
            .join(BookFaculty, BookFaculty.faculty_id == Faculty.id)
            .filter(BookFaculty.book_id == book_id, BookFaculty.branch_id == branch_id)
            .order_by(Faculty.name)
            .all()
        ]
        title = session.query(Book.title).filter_by(id=book_id).scalar()
        bname = session.query(Branch.name).filter_by(id=branch_id).scalar()
    return render_template("book_faculties.html", title=title, branch=bname, count=count, names=names)

# 3) Книги: список
@app.route("/books")
def books_list():
    with SessionLocal() as session:
        books = (
            session.query(
                Book.id, Book.title, Book.year, Book.pages, Book.illustrations, Book.price, Publisher.name.label("publisher")
            )
            .outerjoin(Publisher, Publisher.id == Book.publisher_id)
            .order_by(Book.title)
            .all()
        )
    return render_template("books.html", books=books)

# 3) Книги: форма add/edit
@app.route("/books/add", methods=["GET", "POST"])
@app.route("/books/<int:book_id>/edit", methods=["GET", "POST"])
def book_form(book_id=None):
    with SessionLocal() as session:
        if request.method == "POST":
            title = request.form.get("title")
            publisher_name = request.form.get("publisher") or None
            year = request.form.get("year", type=int)
            pages = request.form.get("pages", type=int)
            illustrations = request.form.get("illustrations", type=int)
            price = request.form.get("price", type=float)
            authors_raw = request.form.get("authors", "") or ""
            authors_list = [a.strip() for a in authors_raw.split(",") if a.strip()]

            publisher = None
            if publisher_name:
                publisher = session.query(Publisher).filter_by(name=publisher_name).one_or_none()
                if not publisher:
                    publisher = Publisher(name=publisher_name)
                    session.add(publisher)
                    session.flush()

            if book_id:
                book = session.get(Book, book_id)
                book.title = title
                book.publisher = publisher
                book.year = year
                book.pages = pages
                book.illustrations = illustrations or 0
                book.price = price
                # перезапишем авторов
                book.authors.clear()
            else:
                book = Book(
                    title=title,
                    publisher=publisher,
                    year=year,
                    pages=pages,
                    illustrations=illustrations or 0,
                    price=price,
                )
                session.add(book)
                session.flush()

            # авторы
            for full_name in authors_list:
                a = session.query(Author).filter_by(full_name=full_name).one_or_none()
                if not a:
                    a = Author(full_name=full_name)
                    session.add(a)
                    session.flush()
                session.add(BookAuthor(book_id=book.id, author_id=a.id))

            session.commit()
            flash("Книга сохранена", "success")
            return redirect(url_for("books_list"))

        book = None
        authors = ""
        if book_id:
            book = session.get(Book, book_id)
            authors = ", ".join([session.get(Author, ba.author_id).full_name for ba in book.authors])
    return render_template("book_form.html", book=book, authors=authors)

# 4) Филиалы
@app.route("/branches")
def branches_list():
    with SessionLocal() as session:
        branches = session.query(Branch.id, Branch.name, Branch.address).order_by(Branch.name).all()
    return render_template("branches.html", branches=branches)

@app.route("/branches/add", methods=["GET", "POST"])
@app.route("/branches/<int:branch_id>/edit", methods=["GET", "POST"])
def branch_form(branch_id=None):
    with SessionLocal() as session:
        if request.method == "POST":
            name = request.form.get("name")
            address = request.form.get("address")
            if branch_id:
                br = session.get(Branch, branch_id)
                br.name = name
                br.address = address
            else:
                session.add(Branch(name=name, address=address))
            session.commit()
            flash("Филиал сохранён", "success")
            return redirect(url_for("branches_list"))
        branch = session.get(Branch, branch_id) if branch_id else None
    return render_template("branch_form.html", branch=branch)

# Управление инвентарём (демо для триггера)
@app.route("/inventories", methods=["GET", "POST"])
def inventories():
    with SessionLocal() as session:
        if request.method == "POST":
            book_id = request.form.get("book_id", type=int)
            branch_id = request.form.get("branch_id", type=int)
            copies_total = request.form.get("copies_total", type=int)
            try:
                inv = session.query(Inventory).filter_by(book_id=book_id, branch_id=branch_id).one_or_none()
                if not inv:
                    inv = Inventory(book_id=book_id, branch_id=branch_id, copies_total=copies_total)
                    session.add(inv)
                else:
                    inv.copies_total = copies_total
                session.commit()
                flash("Инвентарь обновлён", "success")
            except Exception as e:
                session.rollback()
                flash(f"Ошибка: {e}", "danger")

        # Коррелированный подзапрос: активные выдачи по той же (book_id, branch_id)
        active_subq = (
            select(func.count(Borrow.id))
            .where(
                Borrow.book_id == Inventory.book_id,
                Borrow.branch_id == Inventory.branch_id,
                Borrow.returned_at.is_(None),
            )
            .correlate(Inventory)
            .scalar_subquery()
        )

        # Один запрос: считаем available = copies_total - COALESCE(active, 0)
        items = (
            session.query(
                Inventory.id,
                Book.title.label("title"),
                Branch.name.label("branch"),
                Inventory.copies_total,
                (Inventory.copies_total - func.coalesce(active_subq, 0)).label("available"),
            )
            .join(Book, Book.id == Inventory.book_id)
            .join(Branch, Branch.id == Inventory.branch_id)
            .order_by(Book.title, Branch.name)
            .all()
        )

        books = session.query(Book.id, Book.title).order_by(Book.title).all()
        branches = session.query(Branch.id, Branch.name).order_by(Branch.name).all()

    return render_template("inventories.html", items=items, books=books, branches=branches)

# 5) Функционал для студентов: выдача / возврат
@app.route("/students")
def students():
    with SessionLocal() as session:
        students = (
            session.query(Student.id, Student.full_name, Faculty.name.label("faculty"))
            .join(Faculty, Faculty.id == Student.faculty_id)
            .order_by(Student.full_name)
            .all()
        )
    return render_template("students.html", students=students)

@app.route("/borrow", methods=["GET", "POST"])
def borrow():
    with SessionLocal() as session:
        if request.method == "POST":
            student_id = request.form.get("student_id", type=int)
            book_id = request.form.get("book_id", type=int)
            branch_id = request.form.get("branch_id", type=int)
            try:
                borrow_book(session, student_id, book_id, branch_id)
                session.commit()
                flash("Книга выдана", "success")
                return redirect(url_for("borrow"))
            except BorrowError as e:
                session.rollback()
                flash(f"Выдача невозможна: {e}", "danger")
            except Exception as e:
                session.rollback()
                flash(f"Ошибка: {e}", "danger")

        students = session.query(Student.id, Student.full_name).order_by(Student.full_name).all()
        books = session.query(Book.id, Book.title).order_by(Book.title).all()
        branches = session.query(Branch.id, Branch.name).order_by(Branch.name).all()

        borrows = (
            session.query(
                Borrow.id,
                Student.full_name.label("student"),
                Book.title.label("book"),
                Branch.name.label("branch"),
                Borrow.borrowed_at,
                Borrow.returned_at,
            )
            .join(Student, Student.id == Borrow.student_id)
            .join(Book, Book.id == Borrow.book_id)
            .join(Branch, Branch.id == Borrow.branch_id)
            .order_by(Borrow.borrowed_at.desc())
            .all()
        )
    return render_template("borrow.html", students=students, books=books, branches=branches, borrows=borrows)

@app.route("/return/<int:borrow_id>", methods=["POST"])
def do_return(borrow_id):
    with SessionLocal() as session:
        br = session.get(Borrow, borrow_id)
        if br and br.returned_at is None:
            br.returned_at = datetime.utcnow()
            session.add(br)
            log_event(session, "BORROW_RETURNED", details=f'{{"borrow_id":{borrow_id}}}')
            session.commit()
            flash("Возврат зарегистрирован", "success")
        else:
            flash("Уже возвращено или не найдено", "warning")
    return redirect(url_for("borrow"))

@app.route("/events")
def events():
    with SessionLocal() as session:
        events = session.query(EventLog).order_by(EventLog.id.desc()).limit(200).all()
    return render_template("events.html", events=events)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7009, debug=True)
