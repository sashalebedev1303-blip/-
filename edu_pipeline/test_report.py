# Регрессионные тесты исправленного модуля отчётности (Этап 7)
# Каждый тест соответствует дефекту из incident_report.md: сначала дефект
# воспроизводился на buggy_report.py, после исправления тест стал зелёным.
import unittest

from fixed_report import average_duration, find_by_status, report_line, top_courses


class TestAverageDuration(unittest.TestCase):

    def test_normal_rows(self):
        rows = [("EDU-1", "enrolled", 10), ("EDU-2", "completed", 20)]
        self.assertEqual(average_duration(rows), 15.0)

    def test_empty_rows_raises(self):
        # раньше было ZeroDivisionError без объяснений
        with self.assertRaises(ValueError):
            average_duration([])


class TestTopCourses(unittest.TestCase):

    def setUp(self):
        self.rows = ([("PY-100",)] * 3 + [("DA-200",)] * 2 + [("QA-150",)])

    def test_returns_most_popular(self):
        # раньше сортировка шла по возрастанию и возвращала худшие курсы
        self.assertEqual(top_courses(self.rows, limit=2),
                         [("PY-100", 3), ("DA-200", 2)])

    def test_limit(self):
        self.assertEqual(len(top_courses(self.rows, limit=1)), 1)


class TestFindByStatus(unittest.TestCase):

    def setUp(self):
        self.rows = [("EDU-1", "enrolled", 36), ("EDU-2", "new", 24)]

    def test_filters_by_status(self):
        result = find_by_status(self.rows, "new")
        self.assertEqual(result, [("EDU-2", "new", 24)])

    def test_does_not_mutate_input(self):
        # раньше rows.sort() менял список на месте у вызывающего
        snapshot = list(self.rows)
        find_by_status(self.rows, "new")
        self.assertEqual(self.rows, snapshot)


class TestReportLine(unittest.TestCase):

    def test_string_id(self):
        self.assertEqual(report_line("EDU-202609-0001", "enrolled"),
                         "Заявка EDU-202609-0001 в статусе enrolled")

    def test_non_string_id(self):
        # раньше конкатенация с числом давала TypeError
        self.assertEqual(report_line(123, "new"), "Заявка 123 в статусе new")


if __name__ == "__main__":
    unittest.main()
