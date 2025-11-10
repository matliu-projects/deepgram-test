# Voice Action Pipeline

This project turns voice memos into structured Notion tasks using Deepgram for speech-to-text
and an LLM-powered parser for extracting action items.

## ⚠️ Never commit API keys

The values you shared (Deepgram API key, Notion token, Notion database ID) are **secrets**. Do
not check them into Git or share them publicly. Instead:

1. Create a local `.env` file containing the keys (see the example below).
2. Keep `.env` out of version control. The provided `.gitignore` file already ignores it.
3. Rotate any keys that may have been exposed.

## Getting started

1. Ensure you have Python 3.10 or newer installed.
2. Install dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e .
   ```

   On Windows PowerShell, activate the virtual environment with:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```

3. Create a `.env` file based on `.env.example` and fill in your real credentials.
4. Run your future CLI or scripts from within the virtual environment.

## Project layout

```
src/
  voice_action/
    __init__.py
    utils/
      __init__.py
      config.py
```

`voice_action.utils.config.load_settings` loads the required environment variables and will
raise a helpful error if anything is missing.

As development continues, you can add modules for:

- Audio ingestion and Deepgram transcription.
- LLM-powered extraction of action items.
- Notion API integration for creating database entries.
- Command-line orchestration tying the pieces together.

## Environment variables

Use the `.env.example` file as a template:

```env
DEEPGRAM_API_KEY=your_deepgram_api_key_here
NOTION_TOKEN=your_notion_integration_token_here
NOTION_DATABASE_ID=your_notion_database_id_here
```

Load these automatically via [`python-dotenv`](https://github.com/theskumar/python-dotenv) or export them manually before running scripts.
