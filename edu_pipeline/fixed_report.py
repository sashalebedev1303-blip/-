# Исправленный модуль отчётности (Этап 7)
# Исправленная версия buggy_report.py. Исходный buggy_report.py не изменён,
# работа велась по циклу: воспроизведение -> исправление -> regression test.
# Разбор каждого дефекта - в incident_report.md.
import sqlite3


def load_enrollments(db_path):
    """Читает заявки из базы: (enrollment_id, status, duration_hours).

    Отличие от buggy_report.py: соединение закрывается после чтения.
    """
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(
            "SELECT enrollment_id, status, duration_hours FROM enrollments").fetchall()
    finally:
        conn.close()
    return rows


def average_duration(rows):
    """Средняя длительность по всем заявкам.

    Отличие от buggy_report.py: на пустом списке поднимается ValueError
    с понятной причиной вместо ZeroDivisionError.
    """
    if not rows:
        raise ValueError("no data: rows is empty")
    return sum(hours for _, _, hours in rows) / len(rows)


def top_courses(rows, limit=3):
    """Топ курсов по числу заявок.

    Отличие от buggy_report.py: сортировка по убыванию счётчика
    (reverse=True), раньше возвращались самые непопулярные курсы.
    """
    counts = {}
    for row in rows:
        counts[row[0]] = counts.get(row[0], 0) + 1
    ordered = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
    return ordered[:limit]


def find_by_status(rows, status):
    """Все заявки в заданном статусе (статус - второй элемент кортежа).

    Отличие от buggy_report.py: входной список не мутируется (лишний
    rows.sort() удалён, фильтрация через list comprehension).
    """
    return [row for row in rows if row[1] == status]


def report_line(enrollment_id, status):
    """Строка отчёта; enrollment_id может прийти не строкой из внешнего файла.

    Отличие от buggy_report.py: f-string вместо конкатенации, поэтому
    число-идентификатор больше не вызывает TypeError.
    """
    return f"Заявка {enrollment_id} в статусе {status}"
