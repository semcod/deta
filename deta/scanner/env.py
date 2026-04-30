"""
Dotenv loader and shell-style variable interpolation for compose values.

Supports the same variable syntax that ``docker compose`` uses:

* ``${VAR}``         - substitute value of ``VAR`` (empty string if unset).
* ``${VAR:-default}``- ``default`` if ``VAR`` unset OR empty.
* ``${VAR-default}`` - ``default`` if ``VAR`` unset (empty value kept).
* ``${VAR:+alt}``    - ``alt`` if ``VAR`` set AND non-empty, else empty.
* ``${VAR+alt}``     - ``alt`` if ``VAR`` is set (even if empty), else empty.
* ``${VAR:?msg}``    - value of ``VAR`` (or empty if unset; we don't raise).
* ``$VAR``           - bare-style substitution.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterable

_VAR_PATTERN = re.compile(
    r"""
    \$\{
        (?P<braced>[A-Za-z_][A-Za-z0-9_]*)
        (?:
            (?P<op>:?[-+?])
            (?P<default>[^}]*)
        )?
    \}
    |
    \$(?P<bare>[A-Za-z_][A-Za-z0-9_]*)
    """,
    re.VERBOSE,
)


def load_env_file(path: Path) -> dict[str, str]:
    """Parse a ``KEY=VALUE`` style dotenv file.

    Lines that are blank or start with ``#`` are ignored. ``export`` prefix
    is stripped and surrounding single/double quotes are removed.
    """
    if not path or not Path(path).is_file():
        return {}

    env: dict[str, str] = {}
    for raw_line in Path(path).read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].lstrip()
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and (
            (value[0] == value[-1] == '"') or (value[0] == value[-1] == "'")
        ):
            value = value[1:-1]
        if key:
            env[key] = value
    return env


def discover_env(compose_file: Path, root: Path) -> dict[str, str]:
    """Merge env vars from project root and the compose file's directory.

    Later sources override earlier ones (compose-dir wins over root).
    """
    sources: list[Path] = []
    root_env = Path(root) / ".env"
    compose_env = Path(compose_file).parent / ".env"
    sources.append(root_env)
    try:
        if compose_env.resolve() != root_env.resolve():
            sources.append(compose_env)
    except OSError:
        sources.append(compose_env)

    merged: dict[str, str] = {}
    for source in sources:
        merged.update(load_env_file(source))
    return merged


def merge_env_files(
    base: dict[str, str],
    env_files: Iterable[Path],
) -> dict[str, str]:
    """Layer additional ``env_file:`` declarations on top of ``base``."""
    merged = dict(base)
    for path in env_files:
        merged.update(load_env_file(Path(path)))
    return merged


def interpolate(value: str, env: dict[str, str]) -> str:
    """Apply shell-style substitution to ``value`` using ``env``."""
    if not isinstance(value, str) or "$" not in value:
        return value

    def replace(match: re.Match[str]) -> str:
        name = match.group("braced") or match.group("bare")
        op = match.group("op")
        default = match.group("default") or ""

        if name not in env:
            if op in (":-", "-"):
                return default
            if op in (":+", "+"):
                return ""
            return ""

        current = env[name]
        if op == ":-":
            return default if current == "" else current
        if op == "-":
            return current
        if op == ":+":
            return default if current != "" else ""
        if op == "+":
            return default
        if op in (":?", "?"):
            return current
        return current

    return _VAR_PATTERN.sub(replace, value)


def interpolate_recursive(obj: Any, env: dict[str, str]) -> Any:
    """Recursively interpolate strings inside lists/dicts."""
    if isinstance(obj, str):
        return interpolate(obj, env)
    if isinstance(obj, list):
        return [interpolate_recursive(item, env) for item in obj]
    if isinstance(obj, dict):
        return {key: interpolate_recursive(val, env) for key, val in obj.items()}
    return obj
