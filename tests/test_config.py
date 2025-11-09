from __future__ import annotations

from pathlib import Path

import pytest

from src.utils.config import Settings


def test_settings_from_env_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "DEEPGRAM_API_KEY=test-deepgram",
                "NOTION_API_KEY=test-notion",
                "NOTION_DATABASE_ID=test-db",
                "DEBUG=1",
            ]
        )
    )

    monkeypatch.delenv("DEEPGRAM_API_KEY", raising=False)
    monkeypatch.delenv("NOTION_API_KEY", raising=False)
    monkeypatch.delenv("NOTION_DATABASE_ID", raising=False)
    monkeypatch.delenv("DEBUG", raising=False)

    settings = Settings.from_env_file(str(env_file))

    assert settings.deepgram_api_key == "test-deepgram"
    assert settings.notion_api_key == "test-notion"
    assert settings.notion_database_id == "test-db"
    assert settings.debug is True
