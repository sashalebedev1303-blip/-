"""Запуск всего проекта ОДНОЙ командой:  python run_all.py

Выполняет шаги 1-11 из README по порядку: база, транзакции, ETL, выгрузки,
очередь проверки, нормализация журнала, класс заявки, кодировки, замеры,
тесты и аналитический ноутбук. Если какой-то шаг падает - останавливается
и показывает, какой именно.

Перед прогоном скрипт сам удаляет папку results/ (в ней только результаты,
исходники в data/final/ не трогаются), поэтому каждый запуск - с чистого
состояния. В конце печатает чек-лист ожидаемых файлов.
"""

import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
NOTEBOOK = "report_enrollments.ipynb"

# чтобы Python не оставлял кэш __pycache__ рядом с кодом и исходниками
ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")

STEPS = [
    ("create_db.py", "Шаг 1. Создание базы данных и справочников"),
    ("batch_load.py", "Шаг 2. Пакетная загрузка и доказательство транзакций"),
    ("etl_import.py", "Шаг 3. ETL: приём заявок, отклонения с причинами"),
    ("export_data.py", "Шаг 4. Выгрузки JSON/XML и разбор внешних ответов"),
    ("review_queue.py", "Шаг 5. Очередь проверки: два эквивалентных pipeline"),
    ("normalize_audit.py", "Шаг 6. Нормализация журнала операторов"),
    ("demo.py", "Шаг 7. Демонстрация класса заявки"),
    ("unicode_diagnostics.py", "Шаг 8. Диагностика кодировок"),
    ("measure_performance.py", "Шаг 9. Замеры производительности"),
]

# что обязано появиться в results/ после прогона
EXPECTED = [
    "edu.db", "rejected_enrollments.csv", "etl_report.txt",
    "report.json", "report.xml", "before_after.csv", "expected_actual.csv",
    "pipeline_comparison.md", "transaction_protocol.txt",
    "tests_green_log.txt", "diagnostic_table.csv", "performance.txt",
]


def banner(text):
    print()
    print("=" * 64)
    print(text)
    print("=" * 64)


def run_script(filename, title):
    banner(f"{title}   [{filename}]")
    proc = subprocess.run([sys.executable, filename], cwd=ROOT, env=ENV)
    if proc.returncode != 0:
        sys.exit(f"\n!!! Шаг провалился (код {proc.returncode}): {title}")


def run_tests():
    banner("Шаг 10. Автоматические тесты (unittest discover)")
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-v"],
        cwd=ROOT, env=ENV, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    log = RESULTS / "tests_green_log.txt"
    log.write_text(proc.stdout, encoding="utf-8")
    tail = proc.stdout.strip().splitlines()[-6:]
    print("\n".join(tail))
    if proc.returncode != 0:
        sys.exit("\n!!! Тесты провалились, полный вывод: results/tests_green_log.txt")


def check_python():
    """Проект использует аннотации list[dict] и f-строки: нужен Python 3.10+."""
    if sys.version_info < (3, 10):
        sys.exit(f"!!! Нужен Python 3.10 или новее, а у вас "
                 f"{sys.version_info.major}.{sys.version_info.minor}.\n"
                 "    Поставьте свежий Python с python.org и запустите снова.")


def offer_jupyter_install():
    """Шаг 11 без nbconvert: предлагаем установить пакет прямо сейчас.

    Возвращает True, если установка удалась и можно продолжать. Любой отказ
    (пользователь ответил «нет», нет интернета, нет клавиатуры) - это НЕ
    ошибка прогона: ноутбук уже лежит в проекте выполненным, шаг можно
    сделать позже одной командой, которую мы напечатаем.
    """
    print("Jupyter/nbconvert не установлен - он нужен только для шага 11 (ноутбук).")
    print("Шаги 1-10 уже выполнены и от этого пакета не зависят.")
    try:
        answer = input("Установить сейчас автоматически (нужен интернет)? [Y/n]: ")
    except (EOFError, OSError):
        print("(нет интерактивного ввода - авто-установка пропущена)")
        answer = "n"
    if answer.strip().lower() in ("", "y", "д", "yes", "да", "дa"):
        print("Ставлю пакет:  python -m pip install notebook nbconvert")
        proc = subprocess.run([sys.executable, "-m", "pip", "install",
                               "--disable-pip-version-check", "notebook", "nbconvert"],
                              env=ENV)
        if proc.returncode == 0:
            importlib.invalidate_caches()
            print("Пакет установлен, продолжаю шаг 11.")
            return True
        print("!!! Авто-установка не удалась (нет интернета или pip заблокирован).")
    print()
    print("Это не ошибка: ноутбук уже выполнен и лежит в проекте с выводами.")
    print("Сделать шаг 11 позже самостоятельно:")
    print("  python -m pip install notebook nbconvert")
    print(f"  python -m nbconvert --to notebook --execute {NOTEBOOK} --inplace")
    return False


def run_notebook():
    banner("Шаг 11. Аналитический ноутбук (7 показателей)")
    if importlib.util.find_spec("nbconvert") is None:
        if not offer_jupyter_install():
            return
    # На Windows pip кладёт команды (jupyter-nbconvert.exe и др.) в папку
    # Scripts, которой часто нет в PATH, и тогда "jupyter nbconvert" падает
    # с ошибкой "Jupyter command not found". Запуск "python -m nbconvert"
    # зависит только от самого Python, поэтому пробуем его первым.
    attempts = [
        ("python -m nbconvert",
         [sys.executable, "-m", "nbconvert", "--to", "notebook",
          "--execute", NOTEBOOK, "--inplace"]),
        ("python -m jupyter nbconvert",
         [sys.executable, "-m", "jupyter", "nbconvert", "--to", "notebook",
          "--execute", NOTEBOOK, "--inplace"]),
    ]
    for label, cmd in attempts:
        proc = subprocess.run(cmd, cwd=ROOT, env=ENV, text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if proc.returncode == 0:
            print(proc.stdout.strip()[-500:] if proc.stdout else "(без вывода)")
            return
        print(f"способ '{label}' не сработал, пробую следующий...")
    print(proc.stdout.strip()[-800:] if proc.stdout else "(без вывода)")
    sys.exit("\n!!! Ноутбук не выполнился. Выполните вручную и посмотрите вывод:\n"
             f"  python -m nbconvert --to notebook --execute {NOTEBOOK} --inplace")


def summary():
    banner("ИТОГ: проверка файлов в results/")
    missing = []
    for name in EXPECTED:
        path = RESULTS / name
        if path.exists() and path.stat().st_size > 0:
            print(f"  [OK]     {name}")
        else:
            print(f"  [НЕТ]    {name}")
            missing.append(name)
    print()
    if missing:
        sys.exit(f"!!! Не создались: {', '.join(missing)}")
    print("ГОТОВО: все 12 результатов на месте, исходники data/final/ не тронуты.")
    # Документы этапов - авторские файлы, конвейер их не создаёт,
    # поэтому проверяем отдельно (отсутствие не валит запуск).
    docs = ["schema_notes.md", "exchange_scheme.md", "class_diagram.md",
            "incident_report.md", "encoding_report.md", "README.txt"]
    docs_missing = [d for d in docs if not (ROOT / d).exists()]
    print()
    if docs_missing:
        print("ВНИМАНИЕ: в корне проекта не хватает документов")
        print("(они не пересоздаются конвейером - положите их рядом с run_all.py):")
        for name in docs_missing:
            print(f"  [НЕТ]    {name}")
    else:
        print("Документы этапов на месте: schema_notes.md, exchange_scheme.md,")
        print("class_diagram.md, incident_report.md, encoding_report.md.")


def main():
    check_python()
    banner("ПОЛНЫЙ ПРОГОН edu_pipeline с чистого состояния")
    if RESULTS.exists():
        shutil.rmtree(RESULTS)
        print("папка results/ удалена - всё будет пересоздано")
    for filename, title in STEPS:
        run_script(filename, title)
    run_tests()
    run_notebook()
    summary()


if __name__ == "__main__":
    main()