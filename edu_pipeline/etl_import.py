# ETL-конвейер: сырой CSV -> валидация -> SQLite (Этап 5)
# Extract (чтение CSV) и Validate (validators.py) и Load (batch_load.py)
# разделены; каждая отклонённая строка получает понятную причину.
import csv
from pathlib import Path

import validators
from batch_load import load_enrollments_batch
from create_db import connect, ensure_schema, DB_PATH

DATA = Path(__file__).with_name("data") / "final"
RESULTS = Path(__file__).with_name("results")
REJECTED = RESULTS / "rejected_enrollments.csv"
REPORT = RESULTS / "etl_report.txt"


def extract():
    """Читает сырые заявки из CSV; возвращает список словарей DictReader."""
    with (DATA / "enrollments_raw.csv").open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def split_rows(rows):
    """Валидирует строки и разделяет их на принятые и отклонённые.

    Дубликат - строка с валидными полями, но с уже встречавшимся номером
    заявки. Возвращает (accepted, rejected), rejected: (id, причина).
    """
    accepted = []
    rejected = []
    seen = set()
    for row in rows:
        enrollment_id = (row.get("enrollment_id") or "").strip()
        errors = validators.validate(row)
        if errors:
            rejected.append((enrollment_id, ";".join(errors)))
        elif enrollment_id in seen:
            rejected.append((enrollment_id, "duplicate_enrollment_id"))
        else:
            seen.add(enrollment_id)
            accepted.append(row)
    return accepted, rejected


def to_db_tuple(row):
    """Превращает строку DictReader в кортеж для параметризованной вставки."""
    return (
        row["enrollment_id"].strip(),
        row["student_email"].strip(),
        row["course_code"].strip(),
        row["status"].strip(),
        row["created_date"].strip(),
        float(row["duration_hours"]),
        row["format"].strip(),
    )


def main():
    """Полный прогон ETL: отклонённые -> rejected_enrollments.csv, принятые -> edu.db."""
    RESULTS.mkdir(exist_ok=True)
    rows = extract()
    accepted, rejected = split_rows(rows)

    with REJECTED.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["enrollment_id", "reason"])
        for enrollment_id, reason in rejected:
            w.writerow([enrollment_id, reason])

    con = connect(DB_PATH)
    try:
        ensure_schema(con)
        inserted, skipped, action, error = load_enrollments_batch(
            con, [to_db_tuple(r) for r in accepted])
    finally:
        con.close()

    dup_cnt = sum(1 for _, reason in rejected if reason == "duplicate_enrollment_id")
    lines = [
        f"Прочитано: {len(rows)}",
        f"Принято: {len(accepted)}",
        f"Отклонено: {len(rejected)}",
        f"Дублей в файле: {dup_cnt}",
        f"Новых вставлено при этом запуске: {inserted} "
        f"(повторный запуск вставит 0 - защита от дублей)",
        "",
        "Причины:",
    ]
    for enrollment_id, reason in rejected:
        lines.append(f"  {enrollment_id or '(без номера)'}: {reason}")

    text = "\n".join(lines)
    REPORT.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
