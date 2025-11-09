"""Utilities for working with locally stored audio files.

This module intentionally focuses on file-based audio ingestion instead of
real-time microphone capture. The helpers defined here make it easy to persist
binary audio data to disk and read it back for transcription workflows.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, List, Optional


class AudioInputError(RuntimeError):
    """Raised when audio input operations fail."""


@dataclass
class StoredAudio:
    """Metadata describing an audio file stored on disk."""

    path: Path
    mime_type: Optional[str] = None

    def open(self, mode: str = "rb") -> BinaryIO:
        """Open the stored audio file with the requested mode."""

        return self.path.open(mode)

    def read(self) -> bytes:
        """Read all bytes from the stored audio file."""

        return self.path.read_bytes()


class FileAudioInput:
    """Handle storing and retrieving audio files from a local directory."""

    def __init__(self, storage_directory: Path | str) -> None:
        self.storage_directory = Path(storage_directory).expanduser().resolve()
        self.storage_directory.mkdir(parents=True, exist_ok=True)

    def store(
        self,
        data: bytes,
        filename: str,
        *,
        mime_type: Optional[str] = None,
        overwrite: bool = False,
    ) -> StoredAudio:
        """Persist audio bytes to the storage directory.

        Args:
            data: Raw audio bytes to save to disk.
            filename: Name of the file to create inside the storage directory.
            mime_type: Optional MIME type for the stored audio.
            overwrite: Whether to overwrite an existing file with the same name.

        Returns:
            Metadata describing the stored audio file.

        Raises:
            AudioInputError: If the target file exists and overwrite is False.
        """

        destination = self.storage_directory / filename
        if destination.exists() and not overwrite:
            raise AudioInputError(
                f"Audio file '{destination}' already exists. Pass overwrite=True to replace it."
            )

        destination.write_bytes(data)
        return StoredAudio(path=destination, mime_type=mime_type)

    def add_existing_file(
        self,
        file_path: Path | str,
        *,
        mime_type: Optional[str] = None,
        overwrite: bool = False,
    ) -> StoredAudio:
        """Copy an existing audio file into the storage directory."""

        source = Path(file_path).expanduser().resolve()
        if not source.is_file():
            raise AudioInputError(f"Audio file '{source}' does not exist.")

        destination = self.storage_directory / source.name
        if destination.exists() and not overwrite:
            raise AudioInputError(
                f"Audio file '{destination}' already exists. Pass overwrite=True to replace it."
            )

        if source != destination:
            shutil.copyfile(source, destination)

        return StoredAudio(path=destination, mime_type=mime_type)

    def list_audio(self) -> List[StoredAudio]:
        """Return metadata for all audio files inside the storage directory."""

        audio_files: List[StoredAudio] = []
        for path in sorted(self.storage_directory.iterdir()):
            if path.is_file():
                audio_files.append(StoredAudio(path=path))
        return audio_files

    def open(self, path: Path | str, mode: str = "rb") -> BinaryIO:
        """Open an audio file located within the storage directory."""

        resolved = self._resolve(path)
        return resolved.open(mode)

    def read(self, path: Path | str) -> bytes:
        """Read all bytes from a stored audio file."""

        resolved = self._resolve(path)
        return resolved.read_bytes()

    def _resolve(self, path: Path | str) -> Path:
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = self.storage_directory / candidate

        candidate = candidate.expanduser().resolve()

        try:
            candidate.relative_to(self.storage_directory)
        except ValueError as exc:  # pragma: no cover - defensive guard
            raise AudioInputError(
                f"Audio file '{candidate}' is outside the storage directory {self.storage_directory}."
            ) from exc

        if not candidate.exists():
            raise AudioInputError(f"Audio file '{candidate}' does not exist.")

        return candidate


__all__ = ["AudioInputError", "FileAudioInput", "StoredAudio"]
