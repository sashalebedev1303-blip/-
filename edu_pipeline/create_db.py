# Схема базы данных «НОРД-Класс» (Этап 4)
# Создаёт results/edu.db и загружает в него справочники студентов и курсов.
import csv
import sqlite3
from pathlib import Path

DATA = Path(__file__).with_name("data") / "final"
RESULTS = Path(__file__).with_name("results")
DB_PATH = RESULTS / "edu.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS students(
    student_email   TEXT PRIMARY KEY,
    full_name       TEXT NOT NULL,
    phone           TEXT,
    registered_date TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS courses(
    course_code    TEXT PRIMARY KEY,
    title          TEXT NOT NULL,
    price_rub      INTEGER NOT NULL,
    default_format TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS enrollments(
    enrollment_id  TEXT PRIMARY KEY,
    student_email  TEXT NOT NULL REFERENCES students(student_email),
    course_code    TEXT NOT NULL REFERENCES courses(course_code),
    status         TEXT NOT NULL,
    created_date   TEXT NOT NULL,
    duration_hours REAL NOT NULL,
    format         TEXT NOT NULL
);
"""


def connect(db_path):
    """Открывает соединение SQLite с включённым контролем внешних ключей."""
    con = sqlite3.connect(str(db_path))
    con.execute("PRAGMA foreign_keys = ON")
    return con


def ensure_schema(con):
    """Создаёт таблицы students, courses, enrollments, если их ещё нет."""
    con.executescript(SCHEMA)
    con.commit()


def load_reference_data(con):
    """Загружает справочники студентов и курсов из CSV (повторный запуск не дублирует)."""
    with (DATA / "students.csv").open(encoding="utf-8-sig", newline="") as f:
        students = [(r["student_email"], r["full_name"], r["phone"], r["registered_date"])
                    for r in csv.DictReader(f)]
    con.executemany(
        "INSERT OR IGNORE INTO students(student_email, full_name, phone, registered_date) "
        "VALUES (?, ?, ?, ?)", students)

    with (DATA / "courses.csv").open(encoding="utf-8-sig", newline="") as f:
        courses = [(r["course_code"], r["title"], r["price_rub"], r["default_format"])
                   for r in csv.DictReader(f)]
    con.executemany(
        "INSERT OR IGNORE INTO courses(course_code, title, price_rub, default_format) "
        "VALUES (?, ?, ?, ?)", courses)
    con.commit()
    return len(students), len(courses)


def main():
    """Создаёт базу и справочники; печатает, что получилось."""
    RESULTS.mkdir(exist_ok=True)
    con = connect(DB_PATH)
    try:
        ensure_schema(con)
        students, courses = load_reference_data(con)
        for table in ("students", "courses", "enrollments"):
            cnt = con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"{table}: {cnt} строк")
        print(f"База готова: {DB_PATH.name}")
    finally:
        con.close()


if __name__ == "__main__":
    main()
