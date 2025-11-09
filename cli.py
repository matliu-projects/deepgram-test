"""Command-line interface for the Deepgram-Notion integration project."""

from __future__ import annotations

import argparse
import sys

from src.utils.logging import configure_logging
from src.utils.config import Settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Deepgram audio ingestion to Notion workflow CLI",
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Optional path to a .env file containing configuration overrides.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    configure_logging()
    settings = Settings.from_env_file(args.config)

    parser.print_help()
    # Placeholder for future orchestration code.
    if settings.debug:
        parser.exit(status=0, message="Debug mode enabled. No actions performed.\n")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
