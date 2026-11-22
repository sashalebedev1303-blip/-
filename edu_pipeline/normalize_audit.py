# Нормализация «грязного» журнала операторов (Этап 3)
# Читает data/final/audit_messy.log, приводит каждую строку к единому виду:
# один пробел, одна запятая, кавычки в одном стиле «...».
import csv
import re
from pathlib import Path

DATA = Path(__file__).with_name("data") / "final" / "audit_messy.log"
RESULTS = Path(__file__).with_name("results")
BEFORE_AFTER = RESULTS / "before_after.csv"
EXPECTED_ACTUAL = RESULTS / "expected_actual.csv"

# Разбор строки журнала: уровень, от 1 до нескольких запятых, время, запятые,
# текст. Именованные группы позволяют дальше обращаться к полям по имени.
AUDIT_LINE_RE = re.compile(
    r"(?P<level>INFO|WARNING|ERROR)\s*,+\s*"
    r"(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s*,+\s*"
    r"(?P<msg>.*)"
)

# Парные кавычки '...' или "...": обратная ссылка \1 гарантирует, что открыли
# и закрыли одним и тем же символом. Обе разновидности заменяются на «...».
QUOTES_RE = re.compile(r"([\"'])((?:(?!\1).)*)\1")
DOUBLE_COMMA_RE = re.compile(r"\s*,(?:\s*,)+")
SPACES_RE = re.compile(r"\s+")


def normalize_message(msg):
    """Приводит текст сообщения к единому виду: кавычки, запятые, пробелы."""
    text = QUOTES_RE.sub(lambda m: f"«{m.group(2)}»", msg)
    text = DOUBLE_COMMA_RE.sub(", ", text)
    text = SPACES_RE.sub(" ", text)
    return text.strip()


def parse_line(line):
    """Разбирает строку журнала на уровень, время и нормализованное сообщение.

    Возвращает кортеж (level, ts, msg) или None, если строка не журнал.
    """
    match = AUDIT_LINE_RE.fullmatch(line.strip())
    if not match:
        return None
    return (match.group("level"), match.group("ts"), normalize_message(match.group("msg")))


def main():
    """Читает журнал, пишет before_after.csv и expected_actual.csv, сверяет."""
    RESULTS.mkdir(exist_ok=True)
    raw_lines = []
    with DATA.open(encoding="utf-8-sig") as f:
        for line in f:
            if line.strip():
                raw_lines.append(line.rstrip("\n"))

    # Эталон: как должна выглядеть каждая строка после нормализации
    # (записан заранее человеком, на него сверяется результат программы).
    expected = [
        ("INFO", "2026-10-01 09:14:03", "заявка «EDU-202609-0001» переведена в статус «enrolled» оператором ivanov@example.com"),
        ("WARNING", "2026-10-02 11:40:57", "заявка «EDU-202609-0004» отклонена: некорректный e-mail, повторная отправка не требуется"),
        ("INFO", "2026-10-03 15:02:11", "заявка «EDU-202610-0005» создана; формат обучения: offline"),
        ("ERROR", "2026-10-04 08:19:44", "заявка «EDU-202610-0008» без контактного адреса; статус остаётся «new»"),
        ("INFO", "2026-10-05 17:55:20", "заявка «EDU-202610-0013» принята с ручной правкой длительности"),
        ("WARNING", "2026-10-06 10:31:09", "неизвестный код курса «XX-999» в заявке «EDU-202610-0011»"),
        ("INFO", "2026-10-07 09:05:37", "заявка «EDU-202610-0018» продублирована, дубликат проигнорирован"),
        ("ERROR", "2026-10-08 19:22:48", "заявка «EDU-202610-0017» содержит невалидный адрес «pavlova@example,com»"),
    ]

    actual = []
    with BEFORE_AFTER.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["line_no", "before", "after"])
        for i, raw in enumerate(raw_lines, 1):
            parsed = parse_line(raw)
            if parsed is None:
                after = f"НЕ РАЗОБРАНО: {raw.strip()}"
                record = None
            else:
                after = ", ".join(parsed)
                record = parsed
            w.writerow([i, raw, after])
            actual.append(record)

    matched = 0
    with EXPECTED_ACTUAL.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["line_no", "expected", "actual", "match"])
        for i, (exp, act) in enumerate(zip(expected, actual), 1):
            exp_line = ", ".join(exp)
            act_line = ", ".join(act) if act else "(строка не разобрана)"
            ok = exp == act
            matched += ok
            w.writerow([i, exp_line, act_line, "да" if ok else "НЕТ"])

    print(f"Строк в журнале: {len(raw_lines)}")
    print(f"Совпало с эталоном: {matched} из {len(expected)}")
    if matched == len(expected):
        print("Нормализация: всё совпало")
    else:
        print("Нормализация: есть расхождения, см. expected_actual.csv")


if __name__ == "__main__":
    main()
