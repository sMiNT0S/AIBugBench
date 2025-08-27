from pathlib import Path
import tempfile

from run_benchmark import main


def test_cli_main_smoke():
    """Smoke test main() with an empty tiered submissions directory."""
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp) / "submissions"
        # Create minimal tiered structure
        (base / "reference_implementations").mkdir(parents=True)
        (base / "templates" / "template").mkdir(parents=True)
        (base / "user_submissions").mkdir(parents=True)
        rc = main(["--submissions-dir", str(base)])
        assert rc == 0
