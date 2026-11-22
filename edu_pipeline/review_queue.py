# Очередь проверки заявок (Этап 2): две эквивалентные реализации
# В очередь попадают заявки со статусом new/on_review - их смотрит оператор.
# Исходные данные не мутируются: оба pipeline строят новые списки.
import csv
from collections import Counter, defaultdict, deque
from pathlib import Path

DATA = Path(__file__).with_name("data") / "final"
RESULTS = Path(__file__).with_name("results")
COMPARISON = RESULTS / "pipeline_comparison.md"

NEEDS_REVIEW = {"new", "on_review"}


def load_rows():
    """Читает сырые заявки; словари пересобираются заново, файл не меняется."""
    with (DATA / "enrollments_raw.csv").open(encoding="utf-8-sig", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def row_to_item(row):
    """Превращает строку CSV в элемент очереди (новый словарь, не мутация)."""
    return {
        "enrollment_id": row["enrollment_id"],
        "student_email": row["student_email"],
        "course_code": row["course_code"],
        "created_date": row["created_date"],
        "status": row["status"],
    }


def pipeline_deque(rows):
    """Вариант 1: list comprehension -> deque -> popleft (механика очереди)."""
    items = [row_to_item(r) for r in rows if r["status"] in NEEDS_REVIEW]
    queue = deque(sorted(items, key=lambda item: (item["created_date"], item["enrollment_id"])))
    ordered = []
    while queue:
        ordered.append(queue.popleft())
    return ordered


def pipeline_filter_map(rows):
    """Вариант 2: filter + map + lambda -> sorted (функциональный стиль)."""
    filtered = filter(lambda r: r["status"] in NEEDS_REVIEW, rows)
    mapped = map(row_to_item, filtered)
    return sorted(mapped, key=lambda item: (item["created_date"], item["enrollment_id"]))


def queue_stats(ordered):
    """Статистика очереди: Counter по статусам и defaultdict по курсам."""
    by_status = Counter(item["status"] for item in ordered)
    by_course = defaultdict(list)
    for item in ordered:
        by_course[item["course_code"]].append(item["enrollment_id"])
    return by_status, dict(by_course)


def main():
    """Считает очередь двумя способами, доказывает эквивалентность, пишет таблицу."""
    RESULTS.mkdir(exist_ok=True)
    rows = load_rows()
    snapshot_before = [dict(r) for r in rows]

    queue_a = pipeline_deque(rows)
    queue_b = pipeline_filter_map(rows)
    equal = queue_a == queue_b
    status_a, course_a = queue_stats(queue_a)

    print(f"Строк в файле: {len(rows)}, в очереди проверки: {len(queue_a)}")
    print("Очередь (FIFO по дате создания):")
    for item in queue_a:
        print(f"  {item['created_date']}  {item['enrollment_id']}  "
              f"{item['course_code']}  {item['status']}")
    print("Статусы очереди:", dict(status_a))
    print("Заявки по курсам:", {k: v for k, v in course_a.items()})
    print("pipeline эквивалентны:", equal)
    print("исходные данные не мутированы:", rows == snapshot_before)

    comparison = [
        "| Свойство | pipeline_deque | pipeline_filter_map |",
        "| --- | --- | --- |",
        "| Инструменты | list comprehension, deque, popleft | filter, map, lambda, sorted |",
        "| Идея | очередь как структура (FIFO) | поток данных через функции |",
        "| Сортировка | до постановки в очередь | в конце по тому же ключу |",
        "| Мутация исходных строк | нет | нет |",
        "| Результат | тот же список словарей | тот же список словарей |",
        f"| Эквивалентность | совпало: {equal} | совпало: {equal} |",
    ]
    COMPARISON.write_text("\n".join(comparison) + "\n", encoding="utf-8")
    print(f"Таблица сравнения: {COMPARISON.name}")


if __name__ == "__main__":
    main()
