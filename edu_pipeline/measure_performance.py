# Замеры производительности (Этап 7): timeit для pipeline этапа 2
# Сравниваются две реализации очереди и две механики извлечения из очереди.
import timeit
from collections import deque
from pathlib import Path

from review_queue import load_rows, pipeline_deque, pipeline_filter_map

RESULTS = Path(__file__).with_name("results")
PERFORMANCE = RESULTS / "performance.txt"
SCALE = 50  # во сколько раз увеличиваем данные для заметных замеров


def measure():
    """Возвращает строки протокола с реальными числами timeit."""
    lines = []
    rows = load_rows() * SCALE  # 950 строк: очереди становятся заметными
    lines.append(f"Данные: сырые заявки x{SCALE} = {len(rows)} строк")

    t_deque = min(timeit.repeat(
        lambda: pipeline_deque(rows), repeat=5, number=100)) / 100 * 1000
    t_filter = min(timeit.repeat(
        lambda: pipeline_filter_map(rows), repeat=5, number=100)) / 100 * 1000
    lines.append(f"pipeline_deque      (comprehension + deque):   {t_deque:.3f} мс/вызов")
    lines.append(f"pipeline_filter_map (filter + map + sorted):    {t_filter:.3f} мс/вызов")
    lines.append("Вывод: скорости сопоставимы, выбор по читаемости задачи "
                 "(у deque честная механика очереди FIFO).")

    # deque.popleft() O(1) против list.pop(0) O(n) на большой очереди
    n = 10_000
    t_popleft = min(timeit.repeat(
        stmt="q = deque(range(n))\nwhile q: q.popleft()",
        setup=f"from collections import deque; n = {n}", repeat=5, number=10)) / 10 * 1000
    t_pop0 = min(timeit.repeat(
        stmt="q = list(range(n))\nwhile q: q.pop(0)",
        setup=f"from collections import deque; n = {n}", repeat=5, number=10)) / 10 * 1000
    lines.append("")
    lines.append(f"Механика очереди на {n} элементах (полный слив очереди):")
    lines.append(f"deque.popleft()  O(1): {t_popleft:.2f} мс")
    lines.append(f"list.pop(0)      O(n): {t_pop0:.2f} мс")
    lines.append("Вывод: на больших очередях deque быстрее в разы - "
                 "pop(0) каждый раз сдвигает весь список.")
    return lines


def main():
    """Пишет протокол замеров в results/performance.txt."""
    RESULTS.mkdir(exist_ok=True)
    lines = measure()
    text = "\n".join(lines)
    PERFORMANCE.write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
