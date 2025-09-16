from scripts.update_requirements_lock import _norm_for_compare


def test_header_and_via_normalization():
    src = (
        "# by the following command:\n"
        "#    pip-compile --allow-unsafe ...\n"
        "pkg==1.0  \n"
        "# via mkdocs, click, bandit\n"
        "other==2.0\n"
    )
    out = _norm_for_compare(src)
    assert out == ["pkg==1.0", "# via", "other==2.0"]
