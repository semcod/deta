"""Tests for dotenv loader and shell-style interpolation."""

from pathlib import Path

from deta.scanner.env import interpolate, load_env_file


def test_interpolate_plain():
    assert interpolate("hello", {}) == "hello"


def test_interpolate_simple():
    assert interpolate("${VAR}", {"VAR": "42"}) == "42"


def test_interpolate_default_unset():
    assert interpolate("${VAR:-80}", {}) == "80"


def test_interpolate_default_empty():
    assert interpolate("${VAR:-80}", {"VAR": ""}) == "80"


def test_interpolate_no_default_unset():
    assert interpolate("${VAR-80}", {}) == "80"


def test_interpolate_no_default_empty():
    assert interpolate("${VAR-80}", {"VAR": ""}) == ""


def test_interpolate_plus_alt():
    assert interpolate("${VAR:+alt}", {"VAR": "x"}) == "alt"


def test_interpolate_plus_missing():
    assert interpolate("${VAR:+alt}", {}) == ""


def test_interpolate_bare_dollar():
    assert interpolate("$VAR", {"VAR": "99"}) == "99"


def test_interpolate_embedded():
    assert interpolate("host=${HOST}:port=${PORT}", {"HOST": "127.0.0.1", "PORT": "3306"}) == "host=127.0.0.1:port=3306"


def test_load_env_file(tmp_path: Path):
    env_path = tmp_path / ".env"
    env_path.write_text(
        "# comment\n"
        "FOO=bar\n"
        'BAZ="quoted"\n'
        "export QUX=1\n"
    )
    env = load_env_file(env_path)
    assert env["FOO"] == "bar"
    assert env["BAZ"] == "quoted"
    assert env["QUX"] == "1"
