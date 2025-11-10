"""Configuration loading utilities for the Voice Action project."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv


@dataclass(frozen=True)
class DeepgramSettings:
    """Holds configuration for communicating with Deepgram."""

    api_key: str


@dataclass(frozen=True)
class NotionSettings:
    """Holds configuration for interacting with the Notion API."""

    token: str
    database_id: str


@dataclass(frozen=True)
class Settings:
    """Top-level configuration container for the application."""

    deepgram: DeepgramSettings
    notion: NotionSettings


def _get_env(key: str, default: Optional[str] = None) -> str:
    """Retrieve an environment variable with helpful errors.

    Args:
        key: Environment variable name to load.
        default: Optional default value if the variable is absent.

    Returns:
        The resolved environment variable value.

    Raises:
        RuntimeError: If the variable is required but missing or empty.
    """

    value = os.getenv(key, default)
    if value is None or value.strip() == "":
        raise RuntimeError(
            f"Environment variable '{key}' is required but was not provided."
        )
    return value


def load_settings(dotenv_path: Optional[str] = None) -> Settings:
    """Load configuration values from the environment and optional .env file.

    Args:
        dotenv_path: Path to a .env file to load before reading environment vars.

    Returns:
        A populated :class:`Settings` object.
    """

    load_dotenv(dotenv_path)

    deepgram_settings = DeepgramSettings(
        api_key=_get_env("DEEPGRAM_API_KEY"),
    )

    notion_settings = NotionSettings(
        token=_get_env("NOTION_TOKEN"),
        database_id=_get_env("NOTION_DATABASE_ID"),
    )

    return Settings(deepgram=deepgram_settings, notion=notion_settings)


__all__ = ["DeepgramSettings", "NotionSettings", "Settings", "load_settings"]
