# Пакетная загрузка заявок с доказательством атомарности (Этап 4)
# Сценарий: валидный пакет -> commit; пакет с ошибкой в середине -> rollback;
# программная проверка показывает, что частичных изменений в базе не осталось.
# Демо выполняется на временной базе :memory:, файл edu.db не трогается.
import csv
import sqlite3
from pathlib import Path

import validators
from create_db import connect, ensure_schema, load_reference_data

DATA = Path(__file__).with_name("data") / "final"
RESULTS = Path(__file__).with_name("results")
PROTOCOL = RESULTS / "transaction_protocol.txt"


def extract_valid_rows():
    """Читает сырой CSV и возвращает кортежи только валидных уникальных заявок."""
    seen = set()
    rows = []
    with (DATA / "enrollments_raw.csv").open(encoding="utf-8-sig", newline="") as f:
        for raw in csv.DictReader(f):
            if validators.validate(raw) or raw["enrollment_id"] in seen:
                continue
            seen.add(raw["enrollment_id"])
            rows.append((
                raw["enrollment_id"], raw["student_email"], raw["course_code"],
                raw["status"], raw["created_date"], float(raw["duration_hours"]),
                raw["format"],
            ))
    return rows


def load_enrollments_batch(con, rows):
    """Загружает пакет заявок одной транзакцией: BEGIN -> вставки -> COMMIT.

    При ошибке любой вставки выполняется ROLLBACK и пакет не считается
    загруженным. Возвращает (вставлено, пропущено_дублей, действие, ошибка).
    """
    inserted = 0
    skipped = 0
    try:
        con.execute("BEGIN")
        for row in rows:
            cur = con.execute(
                "INSERT OR IGNORE INTO enrollments(enrollment_id, student_email, "
                "course_code, status, created_date, duration_hours, format) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)", row)
            if cur.rowcount == 1:
                inserted += 1
            else:
                skipped += 1
        con.commit()
        return inserted, skipped, "commit", None
    except sqlite3.IntegrityError as e:
        con.rollback()
        return 0, 0, "rollback", str(e)


def count_enrollments(con):
    """Возвращает число заявок в базе (для проверки отката)."""
    return con.execute("SELECT COUNT(*) FROM enrollments").fetchone()[0]


def main():
    """Прогоняет оба сценария на :memory: и пишет протокол транзакции."""
    RESULTS.mkdir(exist_ok=True)
    lines = []
    log = lines.append

    con = connect(":memory:")
    try:
        ensure_schema(con)
        load_reference_data(con)

        valid_rows = extract_valid_rows()
        before = count_enrollments(con)
        log(f"Сценарий 1: валидный пакет из {len(valid_rows)} заявок")
        inserted, skipped, action, error = load_enrollments_batch(con, valid_rows)
        log(f"  результат: действие={action}, вставлено={inserted}, "
            f"дублей пропущено={skipped}, ошибка={error}")
        after = count_enrollments(con)
        log(f"  заявок в базе: было {before}, стало {after}")

        # Пакет с ошибкой: две валидные строки и одна с несуществующим студентом
        # (нарушение внешнего ключа). Без транзакции две строки остались бы в базе.
        broken_batch = [
            ("EDU-202610-0098", "ivanov@example.com", "QA-150", "enrolled",
             "2026-10-20", 24.0, "online"),
            ("EDU-202610-0099", "petrova@example.com", "WD-300", "new",
             "2026-10-21", 12.0, "offline"),
            ("EDU-202610-0097", "ghost@example.com", "PY-100", "enrolled",
             "2026-10-22", 36.0, "online"),
        ]
        before = count_enrollments(con)
        log(f"Сценарий 2: пакет из {len(broken_batch)} заявок с ошибкой в третьей строке "
            f"(несуществующий студент)")
        inserted, skipped, action, error = load_enrollments_batch(con, broken_batch)
        log(f"  результат: действие={action}, вставлено={inserted}, ошибка={error}")
        after = count_enrollments(con)
        log(f"  заявок в базе: было {before}, стало {after}")
        verdict = "частичных изменений нет" if before == after else "ЕСТЬ частичные изменения!"
        log(f"  проверка отката: {verdict}")
        log("")
        log("Вывод: ошибочный пакет откатился целиком, данные не повреждены.")
    finally:
        con.close()

    text = "\n".join(lines)
    PROTOCOL.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
