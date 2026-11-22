# Демонстрация класса Enrollment (Этап 6)
from enrollment import Enrollment

if __name__ == "__main__":
    ticket = Enrollment("EDU-202610-0005", "kozlov@example.com", "WD-300")
    ticket.status = "on_review"
    ticket.status = "enrolled"
    ticket.status = "completed"

    print("Текущий статус:", ticket.status)
    for entry in ticket.history():
        print(" ", entry)

    # журнал отдаётся копией: чистим копию - история заявки цела
    external = ticket.history()
    external.clear()
    print("После внешнего clear:", len(ticket.history()), "записей в журнале")

    # финальный статус переходов не имеет
    try:
        ticket.status = "new"
    except ValueError as e:
        print("Ожидаемая ошибка:", e)

    # несуществующий статус
    try:
        ticket.status = "paused"
    except ValueError as e:
        print("Ожидаемая ошибка:", e)
