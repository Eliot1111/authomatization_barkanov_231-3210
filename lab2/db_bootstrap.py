# db_bootstrap.py
from sqlalchemy import text
from sqlalchemy.orm import Session

from models import Base, metadata, Publisher, Faculty, Branch, Book, Author, BookAuthor, \
    Inventory, BookFaculty, Student, EventLog

def init_db(engine, with_demo=True):
    """
    Создаёт схему lib (если нет), таблицы ORM, представление v_active_borrows и триггер-валидатор.
    Можно также наполнить демо-данными.
    """
    # 1) Схема и таблицы
    with engine.begin() as conn:
        conn.exec_driver_sql("CREATE SCHEMA IF NOT EXISTS lib;")
    Base.metadata.create_all(engine)

    # 2) Представление активных выдач и триггер-хук
    _create_view_and_triggers(engine)

    # 3) Демо-наполнение (опционально)
    if with_demo:
        _seed_demo(engine)

def _create_view_and_triggers(engine):
    create_view = """
    CREATE OR REPLACE VIEW lib.v_active_borrows AS
    SELECT b.book_id, b.branch_id, COUNT(*)::INT AS active_count
    FROM lib.borrows b
    WHERE b.returned_at IS NULL
    GROUP BY b.book_id, b.branch_id;
    """

    create_trg_func = """
    CREATE OR REPLACE FUNCTION lib.trg_inventories_validate()
    RETURNS TRIGGER AS $$
    BEGIN
      IF NEW.copies_total < 0 THEN
        INSERT INTO lib.event_log(event, details) VALUES
          ('NEGATIVE_INVENTORY_ATTEMPT', to_json(NEW)::text);
        RAISE EXCEPTION 'Количество экземпляров не может быть отрицательным';
      END IF;
      RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """

    create_trigger = """
    DROP TRIGGER IF EXISTS inventories_validate ON lib.inventories;
    CREATE TRIGGER inventories_validate
    BEFORE INSERT OR UPDATE ON lib.inventories
    FOR EACH ROW EXECUTE FUNCTION lib.trg_inventories_validate();
    """

    with engine.begin() as conn:
        conn.exec_driver_sql(create_view)
        conn.exec_driver_sql(create_trg_func)
        conn.exec_driver_sql(create_trigger)

def _seed_demo(engine):
    with Session(engine) as session, session.begin():
        # Издатель
        pub = session.query(Publisher).filter_by(name="Наука").one_or_none()
        if not pub:
            pub = Publisher(name="Наука")
            session.add(pub)

        # Факультеты
        fac_names = ["Физический", "Математический", "Исторический"]
        faculties = {n: session.query(Faculty).filter_by(name=n).one_or_none() or Faculty(name=n)
                     for n in fac_names}
        session.add_all([f for f in faculties.values() if f.id is None])

        # Филиалы
        main = session.query(Branch).filter_by(name="Главный").one_or_none() or Branch(
            name="Главный", address="ул. Университетская, 1"
        )
        br2 = session.query(Branch).filter_by(name="Филиал №2").one_or_none() or Branch(
            name="Филиал №2", address="пр. Науки, 5"
        )
        session.add_all([b for b in (main, br2) if b.id is None])

        # Книги и авторы
        qm = session.query(Book).filter_by(title="Квантовая механика").one_or_none()
        if not qm:
            qm = Book(title="Квантовая механика", publisher=pub, year=2018,
                      pages=520, illustrations=40, price=1250.00)
            session.add(qm)
            a1 = _get_or_create_author(session, "Иванов И.И.")
            a2 = _get_or_create_author(session, "Петров П.П.")
            session.add_all([BookAuthor(book=qm, author=a1), BookAuthor(book=qm, author=a2)])

        he = session.query(Book).filter_by(title="История Европы").one_or_none()
        if not he:
            he = Book(title="История Европы", publisher=pub, year=2015,
                      pages=430, illustrations=16, price=980.00)
            session.add(he)
            a3 = _get_or_create_author(session, "Сидоров С.С.")
            session.add(BookAuthor(book=he, author=a3))

    # Инвентарь и связи факультетов
    with Session(engine) as session, session.begin():
        qm = session.query(Book).filter_by(title="Квантовая механика").one()
        he = session.query(Book).filter_by(title="История Европы").one()
        main = session.query(Branch).filter_by(name="Главный").one()
        br2 = session.query(Branch).filter_by(name="Филиал №2").one()

        _upsert_inventory(session, qm.id, main.id, copies=5)
        _upsert_inventory(session, qm.id, br2.id, copies=5)
        _upsert_inventory(session, he.id, main.id, copies=2)

        phys = session.query(Faculty).filter_by(name="Физический").one()
        math = session.query(Faculty).filter_by(name="Математический").one()

        _upsert_book_faculty(session, qm.id, phys.id, main.id)
        _upsert_book_faculty(session, qm.id, math.id, main.id)

        # Студенты
        if not session.query(Student).filter_by(full_name="Студент 1").one_or_none():
            session.add(Student(full_name="Студент 1", faculty_id=phys.id))
        if not session.query(Student).filter_by(full_name="Студент 2").one_or_none():
            hist = session.query(Faculty).filter_by(name="Исторический").one()
            session.add(Student(full_name="Студент 2", faculty_id=hist.id))

def _get_or_create_author(session: Session, full_name: str) -> Author:
    a = session.query(Author).filter_by(full_name=full_name).one_or_none()
    if not a:
        a = Author(full_name=full_name)
        session.add(a)
        session.flush()
    return a

def _upsert_inventory(session: Session, book_id: int, branch_id: int, copies: int):
    inv = session.query(Inventory).filter_by(book_id=book_id, branch_id=branch_id).one_or_none()
    if not inv:
        inv = Inventory(book_id=book_id, branch_id=branch_id, copies_total=copies)
        session.add(inv)
    else:
        inv.copies_total = copies

def _upsert_book_faculty(session: Session, book_id: int, faculty_id: int, branch_id: int):
    bf = session.query(BookFaculty).filter_by(
        book_id=book_id, faculty_id=faculty_id, branch_id=branch_id
    ).one_or_none()
    if not bf:
        session.add(BookFaculty(book_id=book_id, faculty_id=faculty_id, branch_id=branch_id))
