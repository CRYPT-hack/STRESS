"""Unit tests for STRESS. Run: python3 -m unittest -v test_stress"""

import os
import sys
import tempfile
import unittest
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import grader
import quiz
from questions import BANK, CARDS, Question
import state as st


def make_choice(qid="t1", answer=1):
    return Question(subject="ML", q="Pick one", options=["alpha", "beta", "gamma", "delta"],
                    answer=answer, qid=qid)


class GraderChoice(unittest.TestCase):
    def test_letters_numbers_and_text(self):
        q = make_choice()
        for reply in ("b", "B", "b)", "b.", "2", "  beta ", "BETA"):
            self.assertTrue(grader.grade(q, reply), reply)

    def test_wrong(self):
        q = make_choice()
        for reply in ("a", "c", "d", "3", "5", "zzz", "", "?"):
            self.assertFalse(grader.grade(q, reply), reply)

    def test_fuzzy_option_typo(self):
        q = make_choice(answer=0)
        self.assertTrue(grader.grade(q, "alphaa"))   # insertion typo
        self.assertFalse(grader.grade(q, "gamma"))   # a different option
        self.assertFalse(grader.grade(q, "delta"))

    def test_underfitting_is_not_overfitting(self):
        q = Question(subject="ML", q="?", options=["Overfitting", "Underfitting"],
                     answer=0, qid="t2")
        self.assertTrue(grader.grade(q, "overfitting"))
        self.assertFalse(grader.grade(q, "underfitting"))  # ratio 0.75 < threshold


class GraderOpen(unittest.TestCase):
    def test_normalization(self):
        q = Question(subject="DSA", q="?", options=None, answer=-1,
                     open_answers=["ologn", "logn"], qid="o1")
        self.assertTrue(grader.grade(q, "O(log n)"))
        self.assertTrue(grader.grade(q, "log n"))
        self.assertTrue(grader.grade(q, "(logn)"))
        self.assertFalse(grader.grade(q, "O(n)"))

    def test_numeric(self):
        q = Question(subject="LA", q="?", options=None, answer=-1,
                     open_answers=["7"], qid="o2")
        for reply in ("7", "7.0", " 7 ", "7."):
            self.assertTrue(grader.grade(q, reply), reply)
        self.assertFalse(grader.grade(q, "8"))

    def test_fuzzy_word(self):
        q = Question(subject="ML", q="?", options=None, answer=-1,
                     open_answers=["overfitting"], qid="o3")
        self.assertTrue(grader.grade(q, "over fitting"))
        self.assertFalse(grader.grade(q, "regularization"))

    def test_keywords(self):
        q = Question(subject="ML", q="?", options=None, answer=-1,
                     open_answers=["tp/(tp+fp)"], keywords=["tp", "fp"], qid="o4")
        self.assertTrue(grader.grade(q, "tp divided by tp plus fp"))
        self.assertFalse(grader.grade(q, "tn over tn plus fn"))


class QuizSelection(unittest.TestCase):
    def test_no_repeats_until_exhausted(self):
        pool = [q for q in BANK if q.subject == "ML"]
        asked = set()
        for _ in range(len(pool)):
            q, recycled = quiz.pick_question(BANK, asked, subject="ML")
            self.assertFalse(recycled)
            self.assertEqual(q.subject, "ML")
            asked.add(q.qid)
        self.assertEqual(len(asked), len(pool))
        _, recycled = quiz.pick_question(BANK, asked, subject="ML")
        self.assertTrue(recycled)

    def test_choose_subject(self):
        self.assertEqual(quiz.choose_subject({"ML": 0, "DSA": 1, "LA": 2}), "DSA")
        self.assertIn(quiz.choose_subject({"ML": 0, "DSA": 2, "LA": 2}), ("DSA", "LA"))
        self.assertIsNone(quiz.choose_subject({"ML": 0, "DSA": 0, "LA": 0}))


class StateLogic(unittest.TestCase):
    def test_streak_advances(self):
        s = st.default_state()
        st.ensure_today(s, date(2026, 1, 1))
        self.assertEqual(st.complete_quota(s, date(2026, 1, 1)), 1)
        st.ensure_today(s, date(2026, 1, 2))
        self.assertEqual(st.complete_quota(s, date(2026, 1, 2)), 2)
        self.assertEqual(s["best_streak"], 2)

    def test_complete_quota_idempotent_same_day(self):
        s = st.default_state()
        st.ensure_today(s, date(2026, 1, 1))
        st.complete_quota(s, date(2026, 1, 1))
        self.assertIsNone(st.complete_quota(s, date(2026, 1, 1)))
        self.assertEqual(s["streak"], 1)

    def test_streak_dies_after_gap(self):
        s = st.default_state()
        st.ensure_today(s, date(2026, 1, 1))
        st.complete_quota(s, date(2026, 1, 1))
        st.ensure_today(s, date(2026, 1, 2))
        st.complete_quota(s, date(2026, 1, 2))
        died, missed, old = st.ensure_today(s, date(2026, 1, 5))
        self.assertTrue(died)
        self.assertEqual(missed, 2)
        self.assertEqual(old, 2)
        self.assertEqual(s["streak"], 0)
        self.assertEqual(st.complete_quota(s, date(2026, 1, 5)), 1)

    def test_quota_tracking(self):
        s = st.default_state()
        day = date(2026, 1, 1)
        st.ensure_today(s, day)
        self.assertFalse(st.quota_met(s, day))
        st.record_attempt(s, "ML", True, "ML-001", day)
        st.record_attempt(s, "ML", False, "ML-002", day)
        st.record_attempt(s, "ML", True, "ML-001", day)  # re-ask: counter rises again
        self.assertEqual(st.asked_today(s, "ML", day), 3)
        self.assertFalse(st.quota_met(s, day))  # DSA and LA still untouched
        for subj in ("DSA", "LA"):
            for i in range(3):
                st.record_attempt(s, subj, True, f"{subj}-{i:03d}", day)
        self.assertTrue(st.quota_met(s, day))
        self.assertEqual(st.remaining(s, day), {"ML": 0, "DSA": 0, "LA": 0})

    def test_failed_ids(self):
        s = st.default_state()
        day = date(2026, 1, 1)
        st.ensure_today(s, day)
        st.mark_failed(s, "ML-001", day)
        st.mark_failed(s, "ML-001", day)
        self.assertEqual(st.bucket(s, day)["failed_ids"], ["ML-001"])
        st.clear_failed(s, "ML-001", day)
        self.assertEqual(st.bucket(s, day)["failed_ids"], [])

    def test_save_load_roundtrip(self):
        s = st.default_state()
        s["name"] = "tester"
        s["streak"] = 4
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "state.json")
            st.save(s, path)
            loaded = st.load(path)
            self.assertEqual(loaded["name"], "tester")
            self.assertEqual(loaded["streak"], 4)
            self.assertEqual(loaded["daily_quota"], {"ML": 3, "DSA": 3, "LA": 3})

    def test_totals(self):
        s = st.default_state()
        st.ensure_today(s, date(2026, 1, 1))
        st.record_attempt(s, "ML", True, "a", date(2026, 1, 1))
        st.record_attempt(s, "LA", False, "b", date(2026, 1, 1))
        t = st.totals(s)
        self.assertEqual(t["asked"], 2)
        self.assertEqual(t["correct"], 1)
        self.assertEqual(t["per"]["ML"], {"asked": 1, "correct": 1})
        self.assertEqual(t["days_active"], 1)


class BankSanity(unittest.TestCase):
    def test_bank_shape(self):
        self.assertGreaterEqual(len(BANK), 60)
        ids = [q.qid for q in BANK]
        self.assertEqual(len(ids), len(set(ids)))
        subjects = set()
        for q in BANK:
            self.assertIn(q.subject, ("ML", "DSA", "LA"))
            subjects.add(q.subject)
            self.assertTrue(1 <= q.difficulty <= 3)
            if q.options is not None:
                self.assertTrue(2 <= len(q.options) <= 4)
                self.assertTrue(0 <= q.answer < len(q.options))
            else:
                self.assertTrue(q.open_answers)
                self.assertEqual(q.answer, -1)
            self.assertTrue(q.explanation)
            self.assertTrue(q.qid)
        self.assertEqual(subjects, {"ML", "DSA", "LA"})

    def test_cards(self):
        self.assertGreaterEqual(len(CARDS), 10)
        for key, card in CARDS.items():
            self.assertTrue(card["title"])
            self.assertGreaterEqual(len(card["body"]), 3)


if __name__ == "__main__":
    unittest.main()
