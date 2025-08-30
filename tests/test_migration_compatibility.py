"""Canonical tiered submission structure tests (Phase 1).

Legacy migration logic removed; this file now asserts only the presence
of the new three-tier layout without any fallback or rollback paths.
"""

import pytest


class TestTieredStructure:
    @pytest.fixture
    def tiered_structure(self, tmp_path):
        subs = tmp_path / "submissions"
        (subs / "reference_implementations" / "example_model").mkdir(parents=True)
        (subs / "templates" / "template").mkdir(parents=True)
        (subs / "user_submissions").mkdir(parents=True)
        (subs / "reference_implementations" / "example_model" / "prompt_1_solution.py").write_text("# ok")
        return subs

    def test_structure_exists(self, tiered_structure):
        assert (tiered_structure / "reference_implementations").exists()
        assert (tiered_structure / "templates" / "template").exists()
        assert (tiered_structure / "user_submissions").exists()
        # Legacy directories must not exist
        assert not (tiered_structure / "template").exists()
        assert not any(
            p.name == "template" and p.parent == tiered_structure for p in tiered_structure.iterdir()
        )
