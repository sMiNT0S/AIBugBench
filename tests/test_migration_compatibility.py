"""
Backward compatibility testing for tiered submissions restructure.

Tests migration path for existing users and compatibility layers.
"""

import shutil

import pytest


class TestBackwardCompatibility:
    """Test backward compatibility during migration."""

    @pytest.fixture
    def legacy_submissions_structure(self, tmp_path):
        """Create legacy submissions directory structure."""
        submissions = tmp_path / "submissions"
        submissions.mkdir()

        # Legacy example_model
        example_model = submissions / "example_model"
        example_model.mkdir()
        (example_model / "prompt_1_solution.py").write_text("# Legacy solution")
        (example_model / "prompt_2_config.json").write_text('{"legacy": true}')

        # Legacy template
        template = submissions / "template"
        template.mkdir()
        (template / "README.md").write_text("# Legacy template")

        return submissions

    @pytest.fixture
    def mixed_structure(self, tmp_path):
        """Create mixed legacy/new submissions structure."""
        submissions = tmp_path / "submissions"
        submissions.mkdir()

        # Legacy structure
        example_model = submissions / "example_model"
        example_model.mkdir()
        (example_model / "prompt_1_solution.py").write_text("# Legacy solution")

        # New structure
        ref_impl = submissions / "reference_implementations"
        ref_impl.mkdir()
        new_example = ref_impl / "example_model"
        new_example.mkdir()
        (new_example / "prompt_1_solution.py").write_text("# New solution")

        templates = submissions / "templates"
        templates.mkdir()

        user_subs = submissions / "user_submissions"
        user_subs.mkdir()

        return submissions

    def test_legacy_model_discovery(self, legacy_submissions_structure):
        """Test that legacy models can still be discovered."""
        def legacy_model_finder(submissions_dir):
            """Legacy model discovery logic."""
            models = []

            # Check legacy locations first
            for item in submissions_dir.iterdir():
                if item.is_dir() and item.name not in ['template', '__pycache__', '.git']:
                    if any((item / f).exists() for f in ['prompt_1_solution.py', 'prompt_2_config.json']):
                        models.append(item)

            return models

        models = legacy_model_finder(legacy_submissions_structure)
        assert len(models) == 1
        assert models[0].name == "example_model"

    def test_hybrid_model_discovery(self, mixed_structure):
        """Test model discovery in hybrid legacy/new structure."""
        def hybrid_model_finder(submissions_dir):
            """Hybrid model discovery that checks both old and new locations."""
            models = []

            # Check new structure first
            ref_impl = submissions_dir / "reference_implementations"
            if ref_impl.exists():
                models.extend([m for m in ref_impl.iterdir() if m.is_dir()])

            user_subs = submissions_dir / "user_submissions"
            if user_subs.exists():
                models.extend([m for m in user_subs.iterdir() if m.is_dir()])

            # Fall back to legacy structure
            for item in submissions_dir.iterdir():
                if (item.is_dir() and
                    item.name not in ['reference_implementations', 'templates', 'user_submissions', 'template', '__pycache__', '.git'] and
                    any((item / f).exists() for f in ['prompt_1_solution.py', 'prompt_2_config.json'])):
                    models.append(item)

            return models

        models = hybrid_model_finder(mixed_structure)
        assert len(models) >= 2  # Should find both legacy and new models

    def test_deprecation_warnings(self, legacy_submissions_structure):
        """Test that deprecation warnings are shown for legacy structure."""
        def check_legacy_structure(submissions_dir):
            """Check for legacy structure and emit warnings."""
            warnings_issued = []

            # Check for legacy models
            for item in submissions_dir.iterdir():
                if (item.is_dir() and
                    item.name not in ['reference_implementations', 'templates', 'user_submissions', 'template'] and
                    any((item / f).exists() for f in ['prompt_1_solution.py', 'prompt_2_config.json'])):

                    warning_msg = f"Model '{item.name}' found in legacy location. Consider moving to user_submissions/ or reference_implementations/"
                    warnings_issued.append(warning_msg)

            return warnings_issued

        warnings_list = check_legacy_structure(legacy_submissions_structure)
        assert len(warnings_list) == 1
        assert "example_model" in warnings_list[0]
        assert "legacy location" in warnings_list[0]

    def test_migration_guidance(self, legacy_submissions_structure):
        """Test migration guidance for users with legacy structure."""
        def generate_migration_guidance(submissions_dir):
            """Generate step-by-step migration guidance."""
            guidance = []

            # Find models that need migration
            legacy_models = []
            for item in submissions_dir.iterdir():
                if (item.is_dir() and
                    item.name not in ['reference_implementations', 'templates', 'user_submissions', 'template'] and
                    any((item / f).exists() for f in ['prompt_1_solution.py'])):
                    legacy_models.append(item.name)

            if legacy_models:
                guidance.append("Migration Required - Legacy Structure Detected")
                guidance.append("=" * 50)
                guidance.append("")
                guidance.append("Models found in legacy locations:")
                for model in legacy_models:
                    guidance.append(f"  - {model}/")

                guidance.append("")
                guidance.append("Migration Steps:")
                guidance.append("1. Create new directory structure:")
                guidance.append("   mkdir -p submissions/user_submissions")
                guidance.append("   mkdir -p submissions/reference_implementations")
                guidance.append("   mkdir -p submissions/templates")
                guidance.append("")

                for model in legacy_models:
                    guidance.append(f"2. Move {model} to appropriate location:")
                    guidance.append(f"   mv submissions/{model} submissions/user_submissions/{model}")

                guidance.append("")
                guidance.append("3. Update your commands:")
                guidance.append("   OLD: python run_benchmark.py --model example_model")
                guidance.append("   NEW: python run_benchmark.py --model user_submissions/example_model")

            return guidance

        guidance = generate_migration_guidance(legacy_submissions_structure)
        assert len(guidance) > 10
        assert "Migration Required" in guidance[0]
        assert "example_model" in "\n".join(guidance)

    def test_template_compatibility(self, legacy_submissions_structure):
        """Test template access during transition period."""
        def find_template(submissions_dir):
            """Find template in legacy or new location."""
            template_locations = [
                submissions_dir / "templates" / "template",  # New location
                submissions_dir / "template",  # Legacy location
            ]

            for location in template_locations:
                if location.exists():
                    return location

            return None

        template_path = find_template(legacy_submissions_structure)
        assert template_path is not None
        assert template_path.name == "template"
        assert (template_path / "README.md").exists()

    def test_configuration_migration(self, tmp_path):
        """Test migration of configuration references."""
        config_content = '''
        [tool.aibugbench]
        submissions_dir = "submissions"
        example_model = "submissions/example_model"
        template_dir = "submissions/template"
        '''

        config_file = tmp_path / "pyproject.toml"
        config_file.write_text(config_content)

        # Test configuration update logic
        def update_config_references(config_text):
            """Update configuration to use new structure."""
            updates = {
                'submissions/example_model': 'submissions/reference_implementations/example_model',
                'submissions/template': 'submissions/templates/template',
            }

            updated_config = config_text
            for old_path, new_path in updates.items():
                updated_config = updated_config.replace(old_path, new_path)

            return updated_config

        updated_config = update_config_references(config_content)
        assert "reference_implementations/example_model" in updated_config
        assert "templates/template" in updated_config

    def test_import_compatibility(self, legacy_submissions_structure):
        """Test that imports work from both legacy and new locations."""
        # Create a model with imports
        example_model = legacy_submissions_structure / "example_model"

        solution_code = '''
from pathlib import Path
import sys

# This should work regardless of location
def get_model_info():
    return {
        "name": "example_model",
        "location": str(Path(__file__).parent),
        "type": "legacy" if "reference_implementations" not in str(Path(__file__)) else "reference"
    }
        '''

        (example_model / "prompt_1_solution.py").write_text(solution_code)

        # Test dynamic import
        def test_import_from_path(model_path):
            """Test importing a solution from given path."""
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    "solution",
                    model_path / "prompt_1_solution.py"
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                return module.get_model_info()
            except Exception as e:
                return {"error": str(e)}

        model_info = test_import_from_path(example_model)
        assert "error" not in model_info
        assert model_info["name"] == "example_model"
        assert "legacy" in model_info["type"]


class TestMigrationUtilities:
    """Test utilities to help with migration process."""

    def test_migration_validator(self, tmp_path):
        """Test validation of migration completeness."""
        submissions = tmp_path / "submissions"
        submissions.mkdir()

        def validate_migration_status(submissions_dir):
            """Validate migration status and completeness."""
            status = {
                "has_legacy_structure": False,
                "has_new_structure": False,
                "migration_needed": False,
                "legacy_models": [],
                "new_models": {
                    "reference_implementations": [],
                    "user_submissions": []
                },
                "issues": []
            }

            # Check for new structure
            new_dirs = ["reference_implementations", "templates", "user_submissions"]
            status["has_new_structure"] = all(
                (submissions_dir / d).exists() for d in new_dirs
            )

            # Check for legacy models
            for item in submissions_dir.iterdir():
                if (
                    item.is_dir()
                    and item.name not in [*new_dirs, "template", "__pycache__", ".git"]
                    and any((item / f).exists() for f in ["prompt_1_solution.py"])
                ):
                    status["legacy_models"].append(item.name)
                    status["has_legacy_structure"] = True

            # Check new structure populations
            if status["has_new_structure"]:
                ref_impl_dir = submissions_dir / "reference_implementations"
                user_subs_dir = submissions_dir / "user_submissions"

                if ref_impl_dir.exists():
                    status["new_models"]["reference_implementations"] = [
                        m.name for m in ref_impl_dir.iterdir() if m.is_dir()
                    ]

                if user_subs_dir.exists():
                    status["new_models"]["user_submissions"] = [
                        m.name for m in user_subs_dir.iterdir() if m.is_dir()
                    ]

            # Determine if migration needed
            status["migration_needed"] = (
                status["has_legacy_structure"] and
                not status["has_new_structure"]
            )

            return status

        # Test empty submissions directory
        empty_status = validate_migration_status(submissions)
        assert not empty_status["has_legacy_structure"]
        assert not empty_status["has_new_structure"]
        assert not empty_status["migration_needed"]

        # Add legacy model
        legacy_model = submissions / "test_model"
        legacy_model.mkdir()
        (legacy_model / "prompt_1_solution.py").write_text("# Test")

        legacy_status = validate_migration_status(submissions)
        assert legacy_status["has_legacy_structure"]
        assert not legacy_status["has_new_structure"]
        assert legacy_status["migration_needed"]
        assert "test_model" in legacy_status["legacy_models"]

    def test_automatic_migration_script(self, tmp_path):
        """Test automatic migration script logic."""
        submissions = tmp_path / "submissions"
        submissions.mkdir()

        # Create legacy structure
        legacy_model = submissions / "user_model"
        legacy_model.mkdir()
        (legacy_model / "prompt_1_solution.py").write_text("# User solution")

        legacy_template = submissions / "template"
        legacy_template.mkdir()
        (legacy_template / "README.md").write_text("# Template")

        def perform_automatic_migration(submissions_dir):
            """Perform automatic migration of legacy structure."""
            migration_log = []

            # Create new structure
            new_dirs = {
                "reference_implementations": submissions_dir / "reference_implementations",
                "templates": submissions_dir / "templates",
                "user_submissions": submissions_dir / "user_submissions"
            }

            for name, path in new_dirs.items():
                if not path.exists():
                    path.mkdir()
                    migration_log.append(f"Created {name}/ directory")

            # Migrate template
            legacy_template = submissions_dir / "template"
            if legacy_template.exists():
                new_template = new_dirs["templates"] / "template"
                shutil.copytree(legacy_template, new_template)
                migration_log.append("Migrated template/ to templates/template/")

            # Migrate user models
            for item in submissions_dir.iterdir():
                if (item.is_dir() and
                    item.name not in ["reference_implementations", "templates", "user_submissions", "template", "__pycache__", ".git"] and
                    any((item / f).exists() for f in ["prompt_1_solution.py"])):

                    dest = new_dirs["user_submissions"] / item.name
                    shutil.copytree(item, dest)
                    migration_log.append(f"Migrated {item.name}/ to user_submissions/{item.name}/")

            return migration_log

        log = perform_automatic_migration(submissions)

        # Verify migration completed
        assert len(log) >= 4  # Should have created 3 dirs + migrated template + migrated model
        assert (submissions / "templates" / "template").exists()
        assert (submissions / "user_submissions" / "user_model").exists()
        assert (submissions / "user_submissions" / "user_model" / "prompt_1_solution.py").exists()

    def test_rollback_capability(self, tmp_path):
        """Test ability to rollback migration if issues occur."""
        submissions = tmp_path / "submissions"
        submissions.mkdir()

        # Create migrated structure
        ref_impl = submissions / "reference_implementations"
        ref_impl.mkdir()
        templates = submissions / "templates"
        templates.mkdir()
        user_subs = submissions / "user_submissions"
        user_subs.mkdir()

        # Add some content
        user_model = user_subs / "test_model"
        user_model.mkdir()
        (user_model / "prompt_1_solution.py").write_text("# Important user work")

        template = templates / "template"
        template.mkdir()
        (template / "README.md").write_text("# Template")

        def rollback_migration(submissions_dir):
            """Rollback migration, preserving user data."""
            rollback_log = []

            # Preserve user submissions by moving to root
            user_subs = submissions_dir / "user_submissions"
            if user_subs.exists():
                for model in user_subs.iterdir():
                    if model.is_dir():
                        dest = submissions_dir / model.name
                        if not dest.exists():
                            shutil.move(str(model), str(dest))
                            rollback_log.append(f"Preserved user model: {model.name}")

            # Remove new structure directories
            new_dirs = ["reference_implementations", "templates", "user_submissions"]
            for dir_name in new_dirs:
                dir_path = submissions_dir / dir_name
                if dir_path.exists():
                    shutil.rmtree(dir_path)
                    rollback_log.append(f"Removed {dir_name}/ directory")

            return rollback_log

        log = rollback_migration(submissions)

        # Verify rollback preserved user data
        assert (submissions / "test_model").exists()
        assert (submissions / "test_model" / "prompt_1_solution.py").exists()
        assert not (submissions / "user_submissions").exists()
        assert not (submissions / "reference_implementations").exists()
        assert not (submissions / "templates").exists()

        # Verify user data content preserved
        content = (submissions / "test_model" / "prompt_1_solution.py").read_text()
        assert "Important user work" in content
