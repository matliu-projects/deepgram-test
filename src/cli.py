"""Command-line entry point for Deepgram to Notion automation."""

from __future__ import annotations

import argparse
import json
import logging
import sys
import tempfile
from pathlib import Path
from typing import Iterable, Sequence

from src.audio.input import AudioInputError, FileAudioInput
from src.integrations.deepgram_client import DeepgramClient, DeepgramClientError
from src.llm import LLMClient
from src.notion import NotionClient, NotionClientError
from src.transcription.models import TranscriptionResult
from src.utils.config import Settings
from src.utils.logging import configure_logging


def build_parser() -> argparse.ArgumentParser:
    """Construct an argument parser for the CLI."""

    parser = argparse.ArgumentParser(
        description="Capture audio, transcribe it with Deepgram, extract action items, and send them to Notion.",
    )
    parser.add_argument(
        "--env-file",
        default=None,
        help="Optional path to a .env file containing configuration overrides.",
    )
    parser.add_argument(
        "--storage-dir",
        type=Path,
        default=None,
        help="Directory used to store captured audio files.",
    )
    parser.add_argument(
        "--mimetype",
        default="audio/wav",
        help="MIME type of the provided audio (default: audio/wav).",
    )
    parser.add_argument(
        "--title",
        default="Meeting Notes",
        help="Title for the Notion page created from the transcript.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print Notion payload instead of sending it to the API.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable verbose logging output for troubleshooting.",
    )

    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument(
        "--file",
        type=Path,
        help="Path to a local audio file to process.",
    )
    source_group.add_argument(
        "--stdin",
        action="store_true",
        help="Read audio bytes from standard input.",
    )

    parser.add_argument(
        "--stdin-filename",
        default="stdin_audio.wav",
        help="Filename to use when storing audio captured from stdin.",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return the exit status code."""

    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    configure_logging(logging.DEBUG if args.debug else None)
    logger = logging.getLogger("src.cli")

    try:
        settings = Settings.from_env_file(args.env_file)
    except RuntimeError as exc:
        logger.error("Failed to load configuration: %s", exc)
        return 1

    storage_dir = args.storage_dir or Path(tempfile.mkdtemp(prefix="audio-input-"))
    audio_input = FileAudioInput(storage_dir)

    try:
        audio_bytes, mimetype, stored_path = _capture_audio(
            audio_input,
            file_path=args.file,
            read_stdin=args.stdin,
            stdin_filename=args.stdin_filename,
            mimetype=args.mimetype,
        )
    except AudioInputError as exc:
        logger.error("Audio capture failed: %s", exc)
        return 1

    logger.debug("Stored audio at %s", stored_path)

    deepgram = DeepgramClient(api_key=settings.deepgram_api_key)

    try:
        transcription = deepgram.transcribe_file(audio_bytes, mimetype)
    except DeepgramClientError as exc:
        logger.error("Transcription request failed: %s", exc)
        return 1

    logger.info("Transcription complete with %d characters", len(transcription.text))

    llm = LLMClient()
    actions = _extract_action_items(transcription, llm)
    if actions:
        logger.info("Extracted %d action items", len(actions))
    else:
        logger.warning("No action items detected in transcript")

    notion_payload = _build_notion_payload(
        database_id=settings.notion_database_id,
        title=args.title,
        transcript=transcription,
        actions=actions,
    )

    if args.dry_run:
        logger.info("Dry run enabled; printing Notion payload")
        print(json.dumps(notion_payload, indent=2, sort_keys=True))
        return 0

    notion = NotionClient(api_key=settings.notion_api_key, database_id=settings.notion_database_id)

    try:
        notion.create_page(notion_payload)
    except NotionClientError as exc:
        logger.error("Failed to create Notion page: %s", exc)
        return 1

    logger.info("Successfully created Notion page")
    return 0


def _capture_audio(
    audio_input: FileAudioInput,
    *,
    file_path: Path | None,
    read_stdin: bool,
    stdin_filename: str,
    mimetype: str,
) -> tuple[bytes, str, Path]:
    """Load audio from disk or stdin using the provided audio input handler."""

    if file_path is not None:
        stored = audio_input.add_existing_file(file_path, mime_type=mimetype, overwrite=True)
        return stored.read(), stored.mime_type or mimetype, stored.path

    if read_stdin:
        data = sys.stdin.buffer.read()
        if not data:
            raise AudioInputError("No audio data received from stdin")
        stored = audio_input.store(
            data,
            stdin_filename,
            mime_type=mimetype,
            overwrite=True,
        )
        return stored.read(), stored.mime_type or mimetype, stored.path

    raise AudioInputError("No audio source provided")


def _extract_action_items(transcription: TranscriptionResult, llm: LLMClient) -> list[str]:
    """Derive actionable items from the transcript using the LLM client."""

    transcript_text = transcription.text.strip()
    if not transcript_text:
        return []

    summary = llm.summarize(transcript_text).strip()
    candidate = summary or transcript_text

    actions: list[str] = []
    for line in candidate.splitlines():
        cleaned = line.strip()
        if not cleaned:
            continue
        cleaned = cleaned.lstrip("-*•0123456789. ").strip()
        if cleaned:
            actions.append(cleaned)

    if not actions and candidate:
        actions.append(candidate.strip())

    return actions


def _build_notion_payload(
    *,
    database_id: str,
    title: str,
    transcript: TranscriptionResult,
    actions: Iterable[str],
) -> dict[str, object]:
    """Create a Notion page payload combining the transcript and action items."""

    action_blocks = [
        {
            "object": "block",
            "type": "bulleted_list_item",
            "bulleted_list_item": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": action},
                    }
                ]
            },
        }
        for action in actions
    ]

    transcript_block = {
        "object": "block",
        "type": "paragraph",
        "paragraph": {
            "rich_text": [
                {
                    "type": "text",
                    "text": {"content": transcript.text[:1990]},
                }
            ]
        },
    }

    children = []
    if action_blocks:
        children.append(
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": "Action Items"},
                        }
                    ]
                },
            }
        )
        children.extend(action_blocks)

    if transcript.text:
        children.append(
            {
                "object": "block",
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [
                        {
                            "type": "text",
                            "text": {"content": "Transcript"},
                        }
                    ]
                },
            }
        )
        children.append(transcript_block)

    payload = {
        "parent": {"database_id": database_id},
        "properties": {
            "Name": {
                "title": [
                    {
                        "type": "text",
                        "text": {"content": title},
                    }
                ]
            }
        },
        "children": children,
    }

    metadata = dict(transcript.metadata)
    if metadata:
        payload["properties"]["Metadata"] = {
            "rich_text": [
                {
                    "type": "text",
                    "text": {
                        "content": json.dumps(metadata, sort_keys=True)[:1990],
                    },
                }
            ]
        }

    return payload


__all__ = [
    "build_parser",
    "main",
    "_capture_audio",
    "_extract_action_items",
    "_build_notion_payload",
]


if __name__ == "__main__":  # pragma: no cover - manual invocation helper
    raise SystemExit(main())
