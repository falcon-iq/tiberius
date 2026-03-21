"""Falcon IQ notification library — email templates and SES integration."""

from __future__ import annotations

import logging
from pathlib import Path

from falconiq_notifications.renderer import TemplateRenderer
from falconiq_notifications.ses_client import SESClient

__all__ = ["SESClient", "TemplateRenderer", "send_templated_email"]

logger = logging.getLogger(__name__)


async def send_templated_email(
    to: str,
    template_name: str,
    template_data: dict,
    subject: str,
    sender_email: str,
    templates_dir: str | Path,
    ses_region: str = "us-east-1",
) -> bool:
    """Render a Jinja2 email template and send it via Amazon SES.

    Returns True on success, False on failure. Never raises.
    """
    try:
        renderer = TemplateRenderer(templates_dir)
        html_body = renderer.render(template_name, template_data)

        client = SESClient(sender_email=sender_email, region=ses_region)
        return await client.send_email(to=to, subject=subject, html_body=html_body)
    except Exception:
        logger.exception("Failed to send templated email '%s' to %s", template_name, to)
        return False
