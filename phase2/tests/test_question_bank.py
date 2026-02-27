"""
Tests for phase2/question_bank.py — section filtering and ID lookup.
Run: pytest Desktop/AHI/phase2/tests/
"""

import pytest

from phase2.question_bank import QUESTIONS, filter_by_sections, get_question


class TestGetQuestion:

    def test_known_id(self):
        q = get_question("L1")
        assert q is not None
        assert q.question_id == "L1"
        assert q.category == "Leadership & Vision"

    def test_unknown_id_returns_none(self):
        assert get_question("DOES_NOT_EXIST") is None

    def test_qualitative_question(self):
        q = get_question("Q_Decision")
        assert q is not None
        assert q.question_type == "qualitative"

    def test_likert_question(self):
        q = get_question("T1")
        assert q is not None
        assert q.question_type == "likert"


class TestFilterBySections:

    def test_empty_sections_returns_all(self):
        result = filter_by_sections([])
        assert len(result) == len(QUESTIONS)

    def test_leadership_section(self):
        result = filter_by_sections(["leadership"])
        ids    = [q.question_id for q in result]
        # Must include leadership questions
        assert "L1" in ids
        assert "L2" in ids
        assert "Q_Decision" in ids  # sections=["leadership","tech"]
        # Must NOT include tech-only questions
        assert "T1" not in ids

    def test_tech_section(self):
        result = filter_by_sections(["tech"])
        ids    = [q.question_id for q in result]
        assert "T1" in ids
        assert "T2" in ids
        assert "D1" in ids   # sections=["data","tech"]
        # Pure leadership questions not included
        assert "L1" not in ids

    def test_hr_section(self):
        result = filter_by_sections(["hr"])
        ids    = [q.question_id for q in result]
        assert "C1" in ids
        assert "Q_Concerns" in ids
        assert "T1" not in ids

    def test_multi_section_no_duplicates(self):
        result = filter_by_sections(["leadership", "tech"])
        ids    = [q.question_id for q in result]
        # Verify no duplicate question IDs
        assert len(ids) == len(set(ids))

    def test_all_sections_returns_all_questions(self):
        all_sections = ["leadership", "tech", "data", "hr"]
        result       = filter_by_sections(all_sections)
        result_ids   = {q.question_id for q in result}
        all_ids      = {q.question_id for q in QUESTIONS}
        assert result_ids == all_ids

    def test_case_insensitive(self):
        lower = filter_by_sections(["tech"])
        upper = filter_by_sections(["TECH"])
        assert [q.question_id for q in lower] == [q.question_id for q in upper]

    def test_order_preserved(self):
        result = filter_by_sections(["tech"])
        # All returned questions should be in the same relative order as QUESTIONS
        tech_ids_expected = [q.question_id for q in QUESTIONS if "tech" in q.sections]
        tech_ids_actual   = [q.question_id for q in result]
        # result is a superset (multi-section questions included), check order
        for i in range(len(tech_ids_actual) - 1):
            idx_a = next(j for j, q in enumerate(QUESTIONS) if q.question_id == tech_ids_actual[i])
            idx_b = next(j for j, q in enumerate(QUESTIONS) if q.question_id == tech_ids_actual[i + 1])
            assert idx_a < idx_b, f"Order violated: {tech_ids_actual[i]} before {tech_ids_actual[i+1]}"
