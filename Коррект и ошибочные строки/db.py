import sqlite3


def get_connection(db_name="service.db"):
    """Подключение к базе данных."""
    return sqlite3.connect(db_name)


def create_table(conn):
    """Создание таблицы, если её нет."""
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            ticket_id TEXT PRIMARY KEY,
            created_at TEXT,
            customer TEXT,
            email TEXT,
            category TEXT,
            status TEXT,
            priority TEXT,
            assignee TEXT,
            hours_spent REAL,
            comment TEXT
        )
    """)
    conn.commit()


def save_valid_tickets(conn, tickets):
    """Сохраняет валидные тикеты. Возвращает количество реально добавленных строк."""
    cursor = conn.cursor()
    inserted_count = 0

    for row in tickets:
        # Пункт 74: INSERT OR IGNORE защищает от дублей по PRIMARY KEY (ticket_id)
        cursor.execute("""
            INSERT OR IGNORE INTO tickets 
            (ticket_id, created_at, customer, email, category, status, priority, assignee, hours_spent, comment)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row['ticket_id'], row['created_at'], row['customer'], row['email'],
            row['category'], row['status'], row['priority'], row['assignee'],
            float(row['hours_spent']), row.get('comment', '')
        ))

        # Если строка добавилась (а не проигнорировалась как дубль)
        if cursor.rowcount > 0:
            inserted_count += 1

    conn.commit()
    return inserted_count