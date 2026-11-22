# Диагностика кодировок (Этап 7)
# names_cp1251.txt не открывается как UTF-8, а names_utf8.txt читается
# только с учётом BOM; неверная кодировка выявляется сравнением с эталоном.
import csv
from pathlib import Path

DATA = Path(__file__).with_name("data") / "final"
RESULTS = Path(__file__).with_name("results")
DIAGNOSTIC_TABLE = RESULTS / "diagnostic_table.csv"

CP1251_FILE = DATA / "names_cp1251.txt"
UTF8_FILE = DATA / "names_utf8.txt"


def read_text(path, encoding):
    """Читает файл в указанной кодировке; возвращает (текст, ошибка).

    Текст None, если декодирование не удалось; ошибка - строка с описанием.
    """
    try:
        return path.read_bytes().decode(encoding), None
    except UnicodeDecodeError as e:
        return None, f"UnicodeDecodeError: {e.reason} (байт 0x{e.object[e.start]:02x})"


def main():
    """Пробует разные кодировки для обоих файлов и пишет diagnostic_table.csv."""
    RESULTS.mkdir(exist_ok=True)
    reference, ref_error = read_text(UTF8_FILE, "utf-8-sig")
    rows = []

    combinations = [
        (CP1251_FILE, "utf-8", "попытка открыть CP1251-файл как UTF-8"),
        (CP1251_FILE, "cp1251", "родная кодировка файла"),
        (UTF8_FILE, "utf-8-sig", "чтение с учётом BOM"),
        (UTF8_FILE, "utf-8", "чтение без учёта BOM"),
        (UTF8_FILE, "cp1251", "попытка открыть UTF-8-файл как CP1251"),
    ]
    for path, encoding, hint in combinations:
        text, error = read_text(path, encoding)
        if error:
            rows.append([path.name, encoding, error, "-", hint])
            continue
        if path == UTF8_FILE and encoding == "utf-8-sig":
            matches, verdict = "эталон", "эталон для сравнения"
        else:
            matches = "да" if text == reference else "нет"
            verdict = "текст совпал с эталоном" if text == reference else \
                "текст не совпал - кодировка неверная"
        rows.append([path.name, encoding, "OK", matches, f"{hint}; {verdict}"])

    with DIAGNOSTIC_TABLE.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["file", "encoding", "result", "matches_reference", "verdict"])
        w.writerows(rows)

    print("Эталон: names_utf8.txt в кодировке utf-8-sig (файл начинается с BOM)")
    for row in rows:
        print(f"  {row[0]} + {row[1]}: {row[2]}, совпадение: {row[3]}")
    print("Вывод: names_cp1251.txt нужно читать как cp1251, "
          "names_utf8.txt - как utf-8-sig (учитывая BOM).")
    print(f"Таблица: {DIAGNOSTIC_TABLE.name}")


if __name__ == "__main__":
    main()
