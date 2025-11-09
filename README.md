# Deepgram Notion Automation

This repository scaffolds an automation pipeline that ingests audio, transcribes it using Deepgram, optionally summarizes the content with an LLM, and stores the result in Notion.

## Development Environment

The project is managed with [Poetry](https://python-poetry.org/). Install dependencies and create the virtual environment with:

```bash
poetry install
```

Activate the environment when running commands such as formatting, linting, or tests.

## Tooling

- **Formatting:** `black`
- **Linting:** `ruff`
- **Testing:** `pytest`

Configuration for these tools lives in `pyproject.toml`.

## Environment Variables

Copy `.env.example` to `.env` and fill in the required secrets before running the application.

```bash
cp .env.example .env
```
