# Deepgram Notion Automation

This repository automates the flow of capturing audio, transcribing it with Deepgram, extracting action items with an LLM helper, and storing the result in Notion.

## Prerequisites

- Python 3.11+
- [Poetry](https://python-poetry.org/) for dependency management

Install dependencies and create the virtual environment:

```bash
poetry install
```

## Configuration

Copy `.env.example` to `.env` and populate the required credentials. The CLI also accepts an `--env-file` argument if you prefer to keep credentials elsewhere.

```bash
cp .env.example .env
```

Required variables:

- `DEEPGRAM_API_KEY`
- `NOTION_API_KEY`
- `NOTION_DATABASE_ID`
- Optional: `DEBUG=true` enables verbose logging

## Running the CLI

Use the CLI to orchestrate audio capture, transcription, action extraction, and Notion insertion.

### Process an audio file

```bash
poetry run python cli.py --file path/to/audio.wav --title "Weekly Sync"
```

### Stream audio from stdin

```bash
cat path/to/audio.wav | poetry run python cli.py --stdin --stdin-filename capture.wav
```

Common options:

- `--dry-run`: print the Notion payload without performing an API call.
- `--mimetype`: override the MIME type sent to Deepgram (defaults to `audio/wav`).
- `--storage-dir`: choose where captured audio files are stored.
- `--debug`: enable detailed logging output.

## Testing

Run the unit and end-to-end tests with:

```bash
poetry run pytest
```

The test suite includes fixtures with recorded audio samples and mocks external services so tests remain deterministic.
