# Аналитические запросы к edu.db (Этап 4)
# Все запросы параметризованы: значения подставляются через ?, конкатенации нет.
from collections import defaultdict


def status_counts(con):
    """Сколько заявок в каждом статусе."""
    cur = con.execute(
        "SELECT status, COUNT(*) AS cnt FROM enrollments GROUP BY status ORDER BY cnt DESC"
    )
    return [dict(zip(["status", "cnt"], row)) for row in cur.fetchall()]


def course_counts(con):
    """Сколько заявок на каждом курсе (с названием курса)."""
    cur = con.execute(
        "SELECT c.course_code, c.title, COUNT(*) AS cnt "
        "FROM enrollments e JOIN courses c ON c.course_code = e.course_code "
        "GROUP BY c.course_code, c.title ORDER BY cnt DESC, c.course_code"
    )
    return [dict(zip(["course_code", "title", "cnt"], row)) for row in cur.fetchall()]


def avg_duration_by_course(con):
    """Средняя длительность обучения по курсам."""
    cur = con.execute(
        "SELECT course_code, ROUND(AVG(duration_hours), 1) AS avg_hours "
        "FROM enrollments GROUP BY course_code ORDER BY course_code"
    )
    return [dict(zip(["course_code", "avg_hours"], row)) for row in cur.fetchall()]


def revenue_by_course(con):
    """Потенциальная выручка: цена курса * число активных заявок (enrolled/completed)."""
    cur = con.execute(
        "SELECT c.course_code, c.title, c.price_rub, COUNT(*) AS paid_cnt, "
        "c.price_rub * COUNT(*) AS revenue "
        "FROM enrollments e JOIN courses c ON c.course_code = e.course_code "
        "WHERE e.status IN (?, ?) "
        "GROUP BY c.course_code, c.title, c.price_rub ORDER BY revenue DESC",
        ("enrolled", "completed"),
    )
    return [dict(zip(["course_code", "title", "price_rub", "paid_cnt", "revenue"], row))
            for row in cur.fetchall()]


def enrollments_by_course(con, course_code):
    """Заявки одного курса; код курса подставляется параметром, не строкой."""
    cur = con.execute(
        "SELECT enrollment_id, student_email, status, created_date, duration_hours "
        "FROM enrollments WHERE course_code = ? ORDER BY created_date",
        (course_code,),
    )
    return [dict(zip(["enrollment_id", "student_email", "status", "created_date",
                      "duration_hours"], row)) for row in cur.fetchall()]


def students_by_status(con, status):
    """Студенты с их заявками в заданном статусе; статус подставляется параметром."""
    cur = con.execute(
        "SELECT s.full_name, s.student_email, e.enrollment_id, c.title "
        "FROM enrollments e "
        "JOIN students s ON s.student_email = e.student_email "
        "JOIN courses c ON c.course_code = e.course_code "
        "WHERE e.status = ? ORDER BY s.full_name",
        (status,),
    )
    return [dict(zip(["full_name", "student_email", "enrollment_id", "course"], row))
            for row in cur.fetchall()]


def group_emails_by_course(con):
    """Группировка почт студентов по курсам через defaultdict (Модуль 2)."""
    groups = defaultdict(list)
    cur = con.execute(
        "SELECT e.course_code, s.student_email FROM enrollments e "
        "JOIN students s ON s.student_email = e.student_email "
        "ORDER BY e.course_code"
    )
    for course_code, email in cur.fetchall():
        groups[course_code].append(email)
    return dict(groups)


def main():
    """Печатает примеры всех запросов на реальной базе."""
    from create_db import connect, DB_PATH

    con = connect(DB_PATH)
    try:
        print("По статусам:", status_counts(con))
        print("По курсам:", course_counts(con)[:3])
        print("Средняя длительность:", avg_duration_by_course(con)[:3])
        print("Выручка:", revenue_by_course(con)[:3])
        print("Курс WD-300:", len(enrollments_by_course(con, "WD-300")), "заявок")
        print("Студенты new:", students_by_status(con, "new"))
    finally:
        con.close()


if __name__ == "__main__":
    main()
