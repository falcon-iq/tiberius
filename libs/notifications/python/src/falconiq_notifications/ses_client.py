"""Async wrapper around boto3 SES for sending HTML emails."""

from __future__ import annotations

import asyncio
import logging
import re

import boto3

logger = logging.getLogger(__name__)


def _strip_html(html: str) -> str:
    """Produce a simple plain-text version by stripping HTML tags."""
    text = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


class SESClient:
    """Amazon SES email sender that runs synchronous boto3 calls off the event loop."""

    def __init__(self, sender_email: str, region: str = "us-east-1") -> None:
        self._sender_email = sender_email
        self._region = region
        self._client = None

    def _get_client(self):
        if self._client is None:
            self._client = boto3.client("ses", region_name=self._region)
        return self._client

    async def send_email(self, to: str, subject: str, html_body: str, text_body: str = "") -> bool:
        """Send an email via SES. Returns True on success, False on failure. Never raises."""
        if not text_body:
            text_body = _strip_html(html_body)

        try:
            await asyncio.to_thread(self._send_sync, to, subject, html_body, text_body)
            logger.info("Email sent successfully to %s (subject: %s)", to, subject)
            return True
        except Exception:
            logger.exception("Failed to send email to %s via SES", to)
            return False

    def _send_sync(self, to: str, subject: str, html_body: str, text_body: str) -> None:
        client = self._get_client()
        client.send_email(
            Source=self._sender_email,
            Destination={"ToAddresses": [to]},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {
                    "Text": {"Data": text_body, "Charset": "UTF-8"},
                    "Html": {"Data": html_body, "Charset": "UTF-8"},
                },
            },
        )
