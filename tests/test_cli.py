from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any

import pytest

from src.cli import main
from src.transcription.models import TranscriptionResult


@pytest.fixture
def sample_audio_bytes() -> bytes:
    """Return deterministic audio-like bytes for CLI tests."""

    # The specific bytes are not important to the tests; they simply need to
    # resemble binary audio data so the CLI reads a non-empty payload.
    return (
        b"RIFF$\x00\x00\x00WAVEfmt "
        b"\x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00"  # 44.1kHz mono
        b"\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
    )


@pytest.fixture
def sample_audio_path(tmp_path: Path, sample_audio_bytes: bytes) -> Path:
    """Create a temporary audio file populated with fixture bytes."""

    audio_path = tmp_path / "sample.wav"
    audio_path.write_bytes(sample_audio_bytes)
    return audio_path


def test_cli_file_input_dry_run(
    monkeypatch: pytest.MonkeyPatch,
    sample_audio_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("DEEPGRAM_API_KEY", "test-deepgram")
    monkeypatch.setenv("NOTION_API_KEY", "test-notion")
    monkeypatch.setenv("NOTION_DATABASE_ID", "test-db")

    class FakeDeepgramClient:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def transcribe_file(self, audio: bytes, mimetype: str, *, options: dict[str, Any] | None = None) -> TranscriptionResult:
            assert mimetype == "audio/wav"
            assert len(audio) > 0
            return TranscriptionResult(
                text="Send weekly update to the team. Schedule follow-up email.",
                metadata={"confidence": 0.91},
            )

    class FakeLLMClient:
        def __init__(self) -> None:
            self.calls: list[str] = []

        def summarize(self, text: str) -> str:
            self.calls.append(text)
            return "- Send weekly update to the team\n- Schedule follow-up email"

    monkeypatch.setattr("src.cli.DeepgramClient", FakeDeepgramClient)
    fake_llm = FakeLLMClient()
    monkeypatch.setattr("src.cli.LLMClient", lambda: fake_llm)

    exit_code = main([
        "--file",
        str(sample_audio_path),
        "--dry-run",
        "--title",
        "Daily Standup",
    ])

    assert exit_code == 0

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert payload["parent"]["database_id"] == "test-db"
    title = payload["properties"]["Name"]["title"][0]["text"]["content"]
    assert title == "Daily Standup"

    action_items = [
        block["bulleted_list_item"]["rich_text"][0]["text"]["content"]
        for block in payload["children"]
        if block.get("type") == "bulleted_list_item"
    ]
    assert action_items == ["Send weekly update to the team", "Schedule follow-up email"]


def test_cli_stdin_creates_notion_page(
    monkeypatch: pytest.MonkeyPatch,
    sample_audio_bytes: bytes,
) -> None:
    monkeypatch.setenv("DEEPGRAM_API_KEY", "test-deepgram")
    monkeypatch.setenv("NOTION_API_KEY", "test-notion")
    monkeypatch.setenv("NOTION_DATABASE_ID", "test-db")

    class FakeDeepgramClient:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def transcribe_file(self, audio: bytes, mimetype: str, *, options: dict[str, Any] | None = None) -> TranscriptionResult:
            assert mimetype == "audio/wav"
            assert len(audio) == len(sample_audio_bytes)
            return TranscriptionResult(
                text="Call supplier tomorrow.",
            )

    class FakeLLMClient:
        def summarize(self, text: str) -> str:
            return "1. Call supplier tomorrow"

    created_payloads: list[dict[str, Any]] = []

    class FakeNotionClient:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def create_page(self, payload: dict[str, Any]) -> dict[str, Any]:
            created_payloads.append(payload)
            return {"id": "page123"}

    class FakeBuffer(io.BytesIO):
        def __init__(self, data: bytes) -> None:
            super().__init__(data)

    class FakeStdin:
        def __init__(self, data: bytes) -> None:
            self.buffer = FakeBuffer(data)

    monkeypatch.setattr("src.cli.DeepgramClient", FakeDeepgramClient)
    monkeypatch.setattr("src.cli.LLMClient", FakeLLMClient)
    monkeypatch.setattr("src.cli.NotionClient", FakeNotionClient)
    monkeypatch.setattr("sys.stdin", FakeStdin(sample_audio_bytes))

    exit_code = main([
        "--stdin",
        "--stdin-filename",
        "voice.wav",
    ])

    assert exit_code == 0
    assert created_payloads, "Notion payload should be created"
    payload = created_payloads[0]

    assert payload["parent"]["database_id"] == "test-db"
    action_blocks = [
        block
        for block in payload["children"]
        if block.get("type") == "bulleted_list_item"
    ]
    assert len(action_blocks) == 1
    assert action_blocks[0]["bulleted_list_item"]["rich_text"][0]["text"]["content"] == "Call supplier tomorrow"
