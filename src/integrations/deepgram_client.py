from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Iterator, List, Optional
from urllib.parse import urlencode

import requests

try:
    from websocket import (
        WebSocketConnectionClosedException,
        WebSocketException,
        create_connection,
    )
except ImportError:  # pragma: no cover - optional dependency
    class WebSocketException(RuntimeError):
        """Fallback exception when websocket-client is unavailable."""

    class WebSocketConnectionClosedException(WebSocketException):
        """Fallback exception when websocket-client is unavailable."""

    create_connection = None  # type: ignore[assignment]

from src.transcription.models import TranscriptSegment, TranscriptionResult


DEFAULT_REST_ENDPOINT = "https://api.deepgram.com/v1/listen"
DEFAULT_WEBSOCKET_ENDPOINT = "wss://api.deepgram.com/v1/listen"


class DeepgramClientError(RuntimeError):
    """Raised when the Deepgram API returns an error."""


@dataclass
class DeepgramClient:
    """Thin wrapper around the Deepgram REST and WebSocket APIs."""

    api_key: Optional[str] = None
    rest_endpoint: str = DEFAULT_REST_ENDPOINT
    websocket_endpoint: str = DEFAULT_WEBSOCKET_ENDPOINT
    timeout: int = 30

    def __post_init__(self) -> None:
        if not self.api_key:
            self.api_key = os.getenv("DEEPGRAM_API_KEY")
        if not self.api_key:
            raise DeepgramClientError(
                "Deepgram API key not provided. Set DEEPGRAM_API_KEY or pass api_key explicitly."
            )

    # REST helpers -----------------------------------------------------------------
    def transcribe_file(
        self,
        audio: bytes,
        mimetype: str,
        *,
        options: Optional[Dict[str, Any]] = None,
    ) -> TranscriptionResult:
        """Submit a full audio file for transcription via the REST API."""

        headers = {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": mimetype,
        }
        params = options or {}

        try:
            response = requests.post(
                self.rest_endpoint,
                headers=headers,
                params=params,
                data=audio,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.RequestException as exc:  # pragma: no cover - network guard
            raise DeepgramClientError("Failed to call Deepgram REST API") from exc

        payload = response.json()
        return self._parse_transcription(payload)

    # WebSocket helpers -------------------------------------------------------------
    def stream_transcription(
        self,
        audio_stream: Iterable[bytes],
        mimetype: str,
        *,
        options: Optional[Dict[str, Any]] = None,
    ) -> Iterator[TranscriptionResult]:
        """Yield transcription results from a streaming WebSocket session."""

        params = urlencode(options or {})
        url = self.websocket_endpoint
        if params:
            url = f"{url}?{params}"

        headers = [
            f"Authorization: Token {self.api_key}",
            f"Content-Type: {mimetype}",
        ]

        if create_connection is None:
            raise DeepgramClientError(
                "websocket-client dependency is required for streaming support"
            )

        try:
            ws = create_connection(url, header=headers, timeout=self.timeout)
        except WebSocketException as exc:  # pragma: no cover - defensive network guard
            raise DeepgramClientError("Failed to open Deepgram WebSocket connection") from exc

        try:
            for chunk in audio_stream:
                if not chunk:
                    continue
                ws.send_binary(chunk)

            ws.send(json.dumps({"type": "CloseStream"}))

            while True:
                try:
                    message = ws.recv()
                except WebSocketConnectionClosedException:
                    break

                if not message:
                    continue

                try:
                    payload = json.loads(message)
                except json.JSONDecodeError:  # pragma: no cover - defensive guard
                    continue

                if not self._contains_transcript(payload):
                    continue

                yield self._parse_transcription(payload)
        except WebSocketException as exc:  # pragma: no cover - defensive network guard
            raise DeepgramClientError("Deepgram WebSocket session failed") from exc
        finally:
            try:
                ws.close()
            except WebSocketException:  # pragma: no cover - defensive guard
                pass

    # Parsing helpers ---------------------------------------------------------------
    def _contains_transcript(self, payload: Dict[str, Any]) -> bool:
        if "results" in payload:
            channels = payload["results"].get("channels", [])
            return bool(channels and channels[0].get("alternatives"))
        if "channel" in payload:
            return bool(payload["channel"].get("alternatives"))
        return False

    def _parse_transcription(self, payload: Dict[str, Any]) -> TranscriptionResult:
        alternatives: List[Dict[str, Any]] = []
        if "results" in payload:
            channels = payload["results"].get("channels", [])
            if channels:
                alternatives = channels[0].get("alternatives", [])
        elif "channel" in payload:
            alternatives = payload["channel"].get("alternatives", [])

        transcript_text = ""
        segments: List[TranscriptSegment] = []
        metadata: Dict[str, Any] = {}

        if alternatives:
            best = alternatives[0]
            transcript_text = best.get("transcript", "")

            for word in best.get("words", []) or []:
                segments.append(
                    TranscriptSegment(
                        text=word.get("punctuated_word")
                        or word.get("word")
                        or "",
                        start=word.get("start"),
                        end=word.get("end"),
                        speaker=word.get("speaker"),
                    )
                )

            metadata = {
                key: value
                for key, value in best.items()
                if key not in {"transcript", "words"}
            }

        return TranscriptionResult(
            text=transcript_text,
            segments=segments,
            metadata=metadata,
            raw=payload,
        )


__all__ = ["DeepgramClient", "DeepgramClientError"]
