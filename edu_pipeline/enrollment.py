# Класс заявки с журналом изменений (Этап 6)
# Внешний код читает статус через property, менять его может только
# через разрешённые переходы; журнал наружу отдаётся только копией.
from datetime import datetime


class Enrollment:
    """Заявка студента на курс с историей изменения статуса.

    Атрибуты enrollment_id, student_email, course_code задаются один раз
    при создании. Статус меняется через property с проверкой переходов,
    каждое успешное изменение попадает в журнал.
    """

    VALID_STATUS = {"new", "enrolled", "on_review", "completed", "cancelled"}

    # Допустимые переходы: из какого статуса в какие можно двигаться.
    # Финальные статусы (completed, cancelled) переходов не имеют.
    TRANSITIONS = {
        "new": {"enrolled", "on_review", "cancelled"},
        "enrolled": {"on_review", "completed", "cancelled"},
        "on_review": {"enrolled", "cancelled"},
        "completed": set(),
        "cancelled": set(),
    }

    def __init__(self, enrollment_id: str, student_email: str,
                 course_code: str, status: str = "new"):
        """Создаёт заявку; начальный статус тоже проходит проверку."""
        self.enrollment_id = enrollment_id
        self.student_email = student_email
        self.course_code = course_code
        if status not in self.VALID_STATUS:
            raise ValueError(f"bad status: {status}")
        self._status = status
        self._history: list[dict] = []

    @property
    def status(self) -> str:
        """Текущий статус заявки; запись идёт через setter с проверкой."""
        return self._status

    @status.setter
    def status(self, new_status: str) -> None:
        """Меняет статус: проверка статуса, проверка перехода, запись в журнал."""
        if new_status not in self.VALID_STATUS:
            raise ValueError(f"bad status: {new_status}")
        if new_status not in self.TRANSITIONS[self._status]:
            raise ValueError(f"bad transition: {self._status} -> {new_status}")
        old = self._status
        self._status = new_status
        self._log("status", old, new_status)

    def _log(self, field: str, old, new) -> None:
        """Приватный метод журнала: кто снаружи вызывает - тот обходит проверку."""
        self._history.append({
            "at": datetime.now().isoformat(timespec="seconds"),
            "field": field,
            "old": old,
            "new": new,
        })

    def history(self) -> list[dict]:
        """Возвращает копию журнала: правки копии не затрагивают историю заявки."""
        return [dict(entry) for entry in self._history]
