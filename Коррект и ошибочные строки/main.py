import csv
import re
from collections import Counter
import db

DB_NAME = "service.db"
INPUT_CSV = "tickets_raw (3).csv"
REJECTED_CSV = "rejected_tickets.csv"

# Пункт 68. Обязательные поля
REQUIRED_FIELDS = ['ticket_id', 'created_at', 'customer', 'email', 'category', 'status', 'priority', 'assignee',
                   'hours_spent']
VALID_STATUSES = {'new', 'in_progress', 'resolved', 'closed'}


# Пункт 69. Валидаторы
def validate_ticket_id(val):
    return "invalid_ticket_id" if not re.match(r"^SRV-\d{6}-\d{4}$", val) else None


def validate_email(val):
    return "invalid_email" if not re.match(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", val) else None


def validate_hours(val):
    try:
        if float(val) < 0:
            return "negative_hours"
    except ValueError:
        return "hours_not_number"
    return None


def validate_status(val):
    return "invalid_status" if val not in VALID_STATUSES else None


def main():
    accepted = []
    rejected = []
    error_counter = Counter()

    # Пункт 67. Чтение через csv.DictReader
    with open(INPUT_CSV, 'r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            errors = []

            # 68. Проверка на пустые обязательные поля
            for field in REQUIRED_FIELDS:
                if not row.get(field):
                    errors.append(f"missing_{field}")

            # 69, 70. Вызов валидаторов и сбор ВСЕХ ошибок
            if row.get('ticket_id'):
                err = validate_ticket_id(row['ticket_id'])
                if err: errors.append(err)

            if row.get('email'):
                err = validate_email(row['email'])
                if err: errors.append(err)

            if row.get('hours_spent'):
                err = validate_hours(row['hours_spent'])
                if err: errors.append(err)

            if row.get('status'):
                err = validate_status(row['status'])
                if err: errors.append(err)

            # 72. Разделение на валидные и невалидные
            if errors:
                row['error_reason'] = ";".join(errors)
                rejected.append(row)
                for e in errors:
                    error_counter[e] += 1
            else:
                accepted.append(row)

    # 72. Сохранение невалидных строк в CSV с указанием причины
    if rejected:
        with open(REJECTED_CSV, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(rejected[0].keys()))
            writer.writeheader()
            writer.writerows(rejected)

    # 71, 74. Загрузка валидных строк в БД
    conn = db.get_connection(DB_NAME)
    db.create_table(conn)
    inserted = db.save_valid_tickets(conn, accepted)
    conn.close()

    # 73. Формирование контрольного отчёта
    total_read = len(accepted) + len(rejected)

    print("=" * 40)
    print("📊 КОНТРОЛЬНЫЙ ОТЧЁТ")
    print("=" * 40)
    print(f"Всего прочитано строк: {total_read}")
    print(f"Валидных строк:        {len(accepted)}")
    print(f"Добавлено в БД:        {inserted} (без учета дублей)")
    print(f"Отклонено:             {len(rejected)}")
    print("-" * 40)
    print("Причины отклонения:")
    for reason, count in error_counter.most_common():
        print(f" - {reason}: {count} шт.")
    print("=" * 40)


if __name__ == "__main__":
    main()