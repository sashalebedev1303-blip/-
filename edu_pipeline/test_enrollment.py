# Тесты класса Enrollment (Этап 7): переходы статусов, журнал, копии
import unittest

from enrollment import Enrollment


class TestEnrollment(unittest.TestCase):

    def setUp(self):
        # общая заявка для всех проверок (Модуль 6)
        self.ticket = Enrollment("EDU-202610-0005", "kozlov@example.com", "WD-300")

    def test_initial_status_new(self):
        self.assertEqual(self.ticket.status, "new")
        self.assertEqual(self.ticket.history(), [])

    def test_valid_path_writes_history(self):
        self.ticket.status = "on_review"
        self.ticket.status = "enrolled"
        history = self.ticket.history()
        self.assertEqual(len(history), 2)
        self.assertEqual(history[-1]["old"], "on_review")
        self.assertEqual(history[-1]["new"], "enrolled")

    def test_final_status_has_no_transitions(self):
        self.ticket.status = "cancelled"
        with self.assertRaises(ValueError):
            self.ticket.status = "new"

    def test_unknown_status_raises(self):
        with self.assertRaises(ValueError):
            self.ticket.status = "paused"

    def test_on_review_cannot_complete(self):
        # из on_review нельзя сразу в completed - только через enrolled
        self.ticket.status = "on_review"
        with self.assertRaises(ValueError):
            self.ticket.status = "completed"

    def test_history_returns_copy(self):
        self.ticket.status = "enrolled"
        external = self.ticket.history()
        external.clear()
        self.assertEqual(len(self.ticket.history()), 1)

    def test_failed_change_not_logged(self):
        # неудачная попытка смены статуса не попадает в журнал
        before = len(self.ticket.history())
        with self.assertRaises(ValueError):
            self.ticket.status = "completed"
        self.assertEqual(len(self.ticket.history()), before)

    def test_bad_initial_status(self):
        with self.assertRaises(ValueError):
            Enrollment("EDU-202610-0005", "kozlov@example.com", "WD-300", "paused")


if __name__ == "__main__":
    unittest.main()
