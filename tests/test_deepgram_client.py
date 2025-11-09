from __future__ import annotations

import json
from typing import Iterable
from unittest.mock import MagicMock

import pytest

import src.integrations.deepgram_client as deepgram_module
from src.integrations.deepgram_client import DeepgramClient, DeepgramClientError


@pytest.fixture(autouse=True)
def clear_env(monkeypatch: pytest.MonkeyPatch) -> Iterable[None]:
    monkeypatch.delenv("DEEPGRAM_API_KEY", raising=False)
    yield
    monkeypatch.delenv("DEEPGRAM_API_KEY", raising=False)


def test_requires_api_key() -> None:
    with pytest.raises(DeepgramClientError):
        DeepgramClient()


def test_reads_api_key_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEEPGRAM_API_KEY", "env-key")

    client = DeepgramClient()

    assert client.api_key == "env-key"


def test_transcribe_file_parses_response(monkeypatch: pytest.MonkeyPatch) -> None:
    client = DeepgramClient(api_key="test-key")

    payload = {
        "results": {
            "channels": [
                {
                    "alternatives": [
                        {
                            "transcript": "hello world",
                            "confidence": 0.94,
                            "words": [
                                {
                                    "word": "hello",
                                    "start": 0.1,
                                    "end": 0.5,
                                    "speaker": "speaker-1",
                                },
                                {
                                    "word": "world",
                                    "start": 0.6,
                                    "end": 1.0,
                                    "speaker": "speaker-1",
                                },
                            ],
                        }
                    ]
                }
            ]
        }
    }

    response = MagicMock()
    response.json.return_value = payload
    response.raise_for_status.return_value = None

    monkeypatch.setattr(deepgram_module.requests, "post", MagicMock(return_value=response))

    result = client.transcribe_file(b"audio-bytes", "audio/wav")

    assert result.text == "hello world"
    assert len(result.segments) == 2
    assert result.metadata["confidence"] == 0.94
    assert result.speakers == {"speaker-1"}


def test_stream_transcription_yields_results(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DEEPGRAM_API_KEY", "ws-key")

    client = DeepgramClient()

    message = json.dumps(
        {
            "channel": {
                "alternatives": [
                    {
                        "transcript": "chunk transcript",
                        "words": [
                            {
                                "punctuated_word": "chunk",
                                "start": 0.0,
                                "end": 0.5,
                            }
                        ],
                    }
                ]
            }
        }
    )

    class DummyWebSocket:
        def __init__(self) -> None:
            self.sent_chunks: list[bytes] = []
            self.closed = False
            self._messages = iter([message])
            self.sent_control: list[str] = []

        def send_binary(self, data: bytes) -> None:
            self.sent_chunks.append(data)

        def send(self, data: str) -> None:
            self.sent_control.append(data)

        def recv(self) -> str:
            try:
                return next(self._messages)
            except StopIteration as exc:  # pragma: no cover - test helper guard
                raise deepgram_module.WebSocketConnectionClosedException() from exc

        def close(self) -> None:
            self.closed = True

    dummy_ws = DummyWebSocket()
    monkeypatch.setattr(
        deepgram_module,
        "create_connection",
        MagicMock(return_value=dummy_ws),
    )

    chunks = [b"audio-chunk"]
    results = list(client.stream_transcription(chunks, "audio/wav"))

    assert len(results) == 1
    assert results[0].text == "chunk transcript"
    assert dummy_ws.sent_chunks == [b"audio-chunk"]
    assert dummy_ws.closed is True
    assert any("CloseStream" in control for control in dummy_ws.sent_control)
