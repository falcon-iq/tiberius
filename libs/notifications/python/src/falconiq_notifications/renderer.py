"""Jinja2 template renderer for email notifications."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader


class TemplateRenderer:
    """Renders Jinja2 HTML templates from a directory on disk."""

    def __init__(self, templates_dir: str | Path) -> None:
        self._env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=True,
        )

    def render(self, template_name: str, data: dict) -> str:
        """Load ``{template_name}.html`` and render it with *data*."""
        template = self._env.get_template(f"{template_name}.html")
        return template.render(**data)
