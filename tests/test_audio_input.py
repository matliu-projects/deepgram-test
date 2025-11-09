from __future__ import annotations

from pathlib import Path

import pytest

from src.audio.input import AudioInputError, FileAudioInput


def test_store_and_read_audio(tmp_path: Path) -> None:
    audio_dir = tmp_path / "audio"
    audio = FileAudioInput(audio_dir)

    stored = audio.store(b"fake-bytes", "sample.wav", mime_type="audio/wav")

    assert stored.path.exists()
    assert stored.read() == b"fake-bytes"
    assert audio.read("sample.wav") == b"fake-bytes"


def test_store_prevents_overwrite(tmp_path: Path) -> None:
    audio = FileAudioInput(tmp_path)
    audio.store(b"one", "clip.wav")

    with pytest.raises(AudioInputError):
        audio.store(b"two", "clip.wav")


def test_add_existing_file(tmp_path: Path) -> None:
    source = tmp_path / "recording.wav"
    source.write_bytes(b"recorded")

    destination_dir = tmp_path / "storage"
    audio = FileAudioInput(destination_dir)

    stored = audio.add_existing_file(source)

    assert stored.path == destination_dir / "recording.wav"
    assert stored.read() == b"recorded"
    assert len(audio.list_audio()) == 1
