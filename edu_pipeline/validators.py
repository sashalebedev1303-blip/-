# Валидация заявок на обучение (Этап 3)
# Правила идут в порядке колонок файла; структурные проверки (лишние/пустые
# колонки) выполняются первыми, потому что без них проверки полей бессмысленны.
import re
from datetime import datetime

# EDU-ГГГГММ-NNNN: год, настоящий месяц 01-12, четырёхзначный номер.
# Именованные группы нужны дальше, чтобы разбирать дату из номера.
ENROLLMENT_RE = re.compile(r"EDU-(?P<year>\d{4})(?P<month>0[1-9]|1[0-2])-(?P<num>\d{4})")
EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
DATE_FORMAT = "%Y-%m-%d"

VALID_STATUS = {"new", "enrolled", "on_review", "completed", "cancelled"}
VALID_FORMAT = {"online", "offline"}
MIN_DURATION = 0.0

# Коды курсов из справочника courses.csv (эталон для проверки course_code).
DEFAULT_CATALOG = {"PY-100", "DA-200", "QA-150", "WD-300", "SE-250"}

REQUIRED_FIELDS = ("enrollment_id", "student_email", "course_code", "status",
                   "created_date", "duration_hours", "format")


def normalize_row(row):
    """Возвращает копию строки с обрезанными пробелами; исходный словарь не меняет."""
    clean = {}
    for key, value in row.items():
        if isinstance(value, str):
            clean[key] = value.strip()
        else:
            clean[key] = value
    return clean


def validate_enrollment_id(value):
    """Проверяет номер заявки EDU-ГГГГММ-NNNN; при ошибке кидает ValueError."""
    if not ENROLLMENT_RE.fullmatch(value or ""):
        raise ValueError("invalid_enrollment_id")
    return True


def validate_email(value):
    """Проверяет адрес почты; при ошибке кидает ValueError."""
    if not EMAIL_RE.fullmatch(value or ""):
        raise ValueError("invalid_email")
    return True


def validate_course_code(value, catalog=DEFAULT_CATALOG):
    """Проверяет код курса по справочнику; при ошибке кидает ValueError."""
    if value not in catalog:
        raise ValueError("unknown_course")
    return True


def validate_status(value):
    """Проверяет статус из разрешённого набора; при ошибке кидает ValueError."""
    if value not in VALID_STATUS:
        raise ValueError("invalid_status")
    return True


def validate_date(value):
    """Проверяет дату в формате ГГГГ-ММ-ДД; при ошибке кидает ValueError."""
    try:
        datetime.strptime(value or "", DATE_FORMAT)
    except ValueError:
        raise ValueError("invalid_date")
    return True


def validate_duration(value):
    """Проверяет длительность: число и не отрицательное; при ошибке кидает ValueError."""
    try:
        hours = float(value)
    except (TypeError, ValueError):
        raise ValueError("invalid_duration")
    if hours < MIN_DURATION:
        raise ValueError("negative_duration")
    return True


def validate_format(value):
    """Проверяет формат обучения; при ошибке кидает ValueError."""
    if value not in VALID_FORMAT:
        raise ValueError("invalid_format")
    return True


def validate(row, catalog=DEFAULT_CATALOG):
    """Собирает ВСЕ ошибки строки в список кодов (пустой список - строка валидна)."""
    row = normalize_row(row)
    errors = []
    # 1) структурные проверки: колонок больше, чем в заголовке (DictReader
    #    кладёт лишние значения под ключ None), или строка короче заголовка
    if None in row:
        errors.append("extra_columns")
    if any(row.get(field) is None for field in REQUIRED_FIELDS):
        errors.append("missing_fields")
        return errors
    # 2) проверка полей слева направо, как в файле
    checks = (
        ("enrollment_id", lambda v: validate_enrollment_id(v)),
        ("student_email", lambda v: validate_email(v)),
        ("course_code", lambda v: validate_course_code(v, catalog)),
        ("status", lambda v: validate_status(v)),
        ("created_date", lambda v: validate_date(v)),
        ("duration_hours", lambda v: validate_duration(v)),
        ("format", lambda v: validate_format(v)),
    )
    for field, check in checks:
        try:
            check(row.get(field))
        except ValueError as e:
            errors.append(str(e))
    return errors
