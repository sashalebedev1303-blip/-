"""Модуль отчётности по заявкам на обучение (передан инженеру сопровождения).

Автор сообщил: «На части реальных данных возникают странные ошибки».
Исходные данные не изменяйте: работайте по циклу воспроизведение -> исправление -> regression test.
"""

import sqlite3


def load_enrollments(db_path):
    """Верните список кортежей (enrollment_id, status, duration_hours)."""
    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT enrollment_id, status, duration_hours FROM enrollments").fetchall()
    return rows


def average_duration(rows):
    """Средняя трудоёмкость по всем записям."""
    total = 0
    for _, _, hours in rows:
        total = total + hours
    return total / len(rows)


def top_courses(rows, limit=3):
    """Топ курсов по числу заявок. rows: список кортежей (course_code, ...)."""
    counts = {}
    for row in rows:
        counts[row[0]] = counts.get(row[0], 0) + 1
    ordered = sorted(counts.items(), key=lambda kv: kv[1])
    return ordered[:limit]


def find_by_status(rows, status):
    """Все заявки с заданным статусом. Мутирует список для ускорения."""
    rows.sort(key=lambda r: r[1])
    return [r for r in rows if r[1] == status]


def report_line(enrollment_id, status):
    """Строка отчёта. enrollment_id приходит из внешнего файла."""
    return "Заявка " + enrollment_id + " в статусе " + status
