"""Notion client abstractions."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

import requests

__all__ = ["NotionClient", "NotionClientError"]


class NotionClientError(RuntimeError):
    """Raised when a Notion API request fails."""


@dataclass
class NotionClient:
    """Minimal client for interacting with the Notion API."""

    api_key: str | None = None
    database_id: str | None = None
    api_base: str = "https://api.notion.com/v1"
    notion_version: str = "2022-06-28"
    timeout: int = 30
    session: requests.Session = field(default_factory=requests.Session)

    def __post_init__(self) -> None:
        if not self.api_key:
            self.api_key = os.getenv("NOTION_API_KEY")
        if not self.database_id:
            self.database_id = os.getenv("NOTION_DATABASE_ID")

        if not self.api_key:
            raise NotionClientError(
                "Notion API key not provided. Set NOTION_API_KEY or pass api_key explicitly."
            )
        if not self.database_id:
            raise NotionClientError(
                "Notion database id not provided. Set NOTION_DATABASE_ID or pass database_id explicitly."
            )

    def create_page(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Create a new page in the configured Notion database."""

        url = f"{self.api_base}/pages"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Notion-Version": self.notion_version,
        }

        try:
            response = self.session.post(url, headers=headers, json=payload, timeout=self.timeout)
            response.raise_for_status()
        except requests.RequestException as exc:  # pragma: no cover - network guard
            raise NotionClientError("Failed to create Notion page") from exc

        return response.json()
