# Тесты валидаторов заявок (Этапы 3 и 7): нормальные, граничные и ошибочные случаи
import unittest

import validators


class TestValidators(unittest.TestCase):

    def setUp(self):
        # общий корректный набор данных (Модуль 6)
        self.valid_row = {
            "enrollment_id": "EDU-202609-0001",
            "student_email": "ivanov@example.com",
            "course_code": "PY-100",
            "status": "enrolled",
            "created_date": "2026-09-14",
            "duration_hours": "36",
            "format": "online",
        }

    # --- enrollment_id ---

    def test_valid_row_no_errors(self):
        self.assertEqual(validators.validate(self.valid_row), [])

    def test_enrollment_id_wrong_prefix(self):
        with self.assertRaises(ValueError):
            validators.validate_enrollment_id("BAD-202609-0001")

    def test_enrollment_id_lowercase(self):
        with self.assertRaises(ValueError):
            validators.validate_enrollment_id("edu-202610-0015")

    def test_enrollment_id_month_boundaries(self):
        # месяцы 01 и 12 существуют, 00 и 13 - нет
        self.assertTrue(validators.validate_enrollment_id("EDU-202601-0001"))
        self.assertTrue(validators.validate_enrollment_id("EDU-202612-0001"))
        with self.assertRaises(ValueError):
            validators.validate_enrollment_id("EDU-202600-0001")
        with self.assertRaises(ValueError):
            validators.validate_enrollment_id("EDU-202613-0001")

    def test_enrollment_id_digit_count(self):
        # в номере ровно 4 цифры: 3 и 5 цифр - за границей
        self.assertTrue(validators.validate_enrollment_id("EDU-202609-9999"))
        with self.assertRaises(ValueError):
            validators.validate_enrollment_id("EDU-202609-004")
        with self.assertRaises(ValueError):
            validators.validate_enrollment_id("EDU-202609-00016")

    # --- student_email ---

    def test_email_double_at(self):
        with self.assertRaises(ValueError):
            validators.validate_email("user@example@@ru")

    def test_email_without_zone(self):
        with self.assertRaises(ValueError):
            validators.validate_email("smirnova@example")

    # --- course_code ---

    def test_course_code_unknown(self):
        with self.assertRaises(ValueError):
            validators.validate_course_code("XX-999")

    # --- status ---

    def test_status_all_valid(self):
        for s in ("new", "enrolled", "on_review", "completed", "cancelled"):
            self.assertTrue(validators.validate_status(s))

    def test_status_unknown(self):
        with self.assertRaises(ValueError):
            validators.validate_status("paused")

    # --- created_date ---

    def test_date_valid_and_bad_format(self):
        self.assertTrue(validators.validate_date("2026-09-14"))
        with self.assertRaises(ValueError):
            validators.validate_date("2026/09/14")

    # --- duration_hours ---

    def test_duration_zero_boundary(self):
        # ноль - граница, валиден
        self.assertTrue(validators.validate_duration("0"))

    def test_duration_negative(self):
        with self.assertRaises(ValueError):
            validators.validate_duration("-5")

    def test_duration_not_number(self):
        with self.assertRaises(ValueError):
            validators.validate_duration("abc")

    # --- format ---

    def test_format_unknown(self):
        with self.assertRaises(ValueError):
            validators.validate_format("hybrid")

    # --- строка целиком ---

    def test_validate_row_collects_all_errors(self):
        # validate собирает ВСЕ ошибки строки, а не первую
        row = dict(self.valid_row)
        row["enrollment_id"] = "EDU-2026AA-0016"
        row["status"] = "paused"
        self.assertEqual(
            validators.validate(row),
            ["invalid_enrollment_id", "invalid_status"])

    def test_validate_row_missing_fields(self):
        # отсутствующее поле отмечается структурной ошибкой
        row = dict(self.valid_row)
        del row["student_email"]
        self.assertEqual(validators.validate(row), ["missing_fields"])

    def test_validate_row_extra_columns(self):
        # лишние колонки DictReader кладёт под ключ None
        row = dict(self.valid_row)
        row[None] = ["лишнее"]
        self.assertEqual(validators.validate(row), ["extra_columns"])


if __name__ == "__main__":
    unittest.main()
