"""Application configuration utilities."""

from __future__ import annotations

import dataclasses
import os
from pathlib import Path
from typing import Mapping


@dataclasses.dataclass(slots=True)
class Settings:
    """Runtime configuration loaded from environment variables."""

    deepgram_api_key: str
    notion_api_key: str
    notion_database_id: str
    debug: bool = False

    @classmethod
    def from_env_file(cls, env_file: str | None = None) -> "Settings":
        """Load settings from environment variables and an optional .env file."""

        candidates: list[Path] = []
        if env_file:
            candidates.append(Path(env_file).expanduser())
        else:
            candidates.append(Path.cwd() / ".env")

        env = dict(os.environ)
        for path in candidates:
            if path.exists():
                env.update(_parse_env_file(path))

        return cls(
            deepgram_api_key=_require(env, "DEEPGRAM_API_KEY"),
            notion_api_key=_require(env, "NOTION_API_KEY"),
            notion_database_id=_require(env, "NOTION_DATABASE_ID"),
            debug=_optional_bool(env, "DEBUG", default=False),
        )


def _parse_env_file(path: Path) -> dict[str, str]:
    overrides: dict[str, str] = {}
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        overrides[key.strip()] = value.strip()
    return overrides


def _require(env: Mapping[str, str], key: str) -> str:
    try:
        value = env[key]
    except KeyError as exc:  # pragma: no cover - simple helper
        raise RuntimeError(f"Missing required environment variable: {key}") from exc
    if not value:
        raise RuntimeError(f"Environment variable '{key}' cannot be empty")
    return value


def _optional_bool(env: Mapping[str, str], key: str, *, default: bool = False) -> bool:
    raw = env.get(key)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}
