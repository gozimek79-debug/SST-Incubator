"""Testy dla Cognitive Research Curriculum v0.7."""

import pytest, sys, os
sys.path.insert(0, '.')

from clos_curriculum.academy.lesson import LessonManifest
from clos_curriculum.academy.levels import create_level_0, create_level_1, create_level_2, get_level, list_levels
from clos_curriculum.laboratory.statistics import compute_ci95, cohens_d, validate_sample_size


class TestLessonManifest:
    def test_create_lesson(self):
        lesson = LessonManifest(lesson_id="L0.1", level=0, name="Test", description="Test lesson")
        assert lesson.lesson_id == "L0.1"
        assert lesson.level == 0
        assert lesson.validate_seeds() == False  # domyślnie 1 seed, min 5

    def test_validate_seeds(self):
        lesson = LessonManifest(lesson_id="L0.1", level=0, name="T", description="D", seeds=[1,2,3,4,5])
        assert lesson.validate_seeds() == True

    def test_to_dict(self):
        lesson = LessonManifest(lesson_id="L0.1", level=0, name="T", description="D")
        d = lesson.to_dict()
        assert d["lesson_id"] == "L0.1"


class TestLevels:
    def test_level_0_has_lessons(self):
        level = create_level_0()
        assert level.total_lessons() == 2
        assert level.total_exam_lessons() == 1

    def test_level_1_has_lessons(self):
        level = create_level_1()
        assert level.total_lessons() >= 1
        assert level.total_exam_lessons() >= 1

    def test_level_2_has_lessons(self):
        level = create_level_2()
        assert level.total_lessons() >= 1
        assert level.total_exam_lessons() >= 1

    def test_get_level(self):
        level = get_level(0)
        assert level.level_id == 0
        assert level.name == "Birth & Sensory Reaction"

    def test_get_invalid_level(self):
        with pytest.raises(ValueError):
            get_level(99)

    def test_list_levels(self):
        levels = list_levels()
        assert 0 in levels
        assert 1 in levels
        assert 2 in levels


class TestStatistics:
    def test_ci95(self):
        stats = compute_ci95([1.0, 2.0, 3.0, 4.0, 5.0])
        assert stats["mean"] == 3.0
        assert stats["n"] == 5
        assert stats["ci95_low"] < stats["mean"] < stats["ci95_high"]

    def test_ci95_empty(self):
        stats = compute_ci95([])
        assert stats["n"] == 0

    def test_cohens_d(self):
        d = cohens_d([1.0, 2.0, 3.0], [4.0, 5.0, 6.0])
        assert abs(d) > 1.0  # Duży efekt

    def test_cohens_d_same(self):
        d = cohens_d([1.0, 2.0, 3.0], [1.0, 2.0, 3.0])
        assert d == 0.0

    def test_validate_sample_size(self):
        check = validate_sample_size([1.0, 2.0, 3.0, 4.0, 5.0], min_n=5)
        assert check["sufficient"] == True

    def test_validate_sample_size_insufficient(self):
        check = validate_sample_size([1.0, 2.0], min_n=5)
        assert check["sufficient"] == False
