"""Optional home-only announcement bar driven by content/announcement.yaml."""
from __future__ import annotations

import html
from pathlib import Path
from urllib.parse import urlsplit

import yaml


def render_home_announcement(project_root: Path) -> str:
    """Render a compact bar, or nothing when disabled/missing.

    Keep it outside the main hero, immediately below the global navigation.
    There is intentionally no sticky behavior or injected JavaScript.
    """
    config = project_root / 'content' / 'announcement.yaml'
    if not config.is_file():
        return ''
    data = yaml.safe_load(config.read_text(encoding='utf-8-sig'))
    if not isinstance(data, dict):
        raise ValueError(f'{config}: expected a YAML mapping')
    enabled = data.get('enabled', False)
    if not isinstance(enabled, bool):
        raise ValueError(f'{config}: enabled must be true or false')
    if not enabled:
        return ''

    message = data.get('text', '')
    if not isinstance(message, str) or not message.strip():
        raise ValueError(f'{config}: text is required when enabled')
    label = data.get('link_text', '')
    url = data.get('url', '')
    if not isinstance(label, str) or not isinstance(url, str):
        raise ValueError(f'{config}: link_text and url must be strings')
    label, url = label.strip(), url.strip()
    if bool(label) != bool(url):
        raise ValueError(f'{config}: link_text and url must either both be set or both be empty')
    link = ''
    if url:
        parsed = urlsplit(url)
        # Allow common external links or internal root-relative pages only.
        if not ((parsed.scheme in ('http', 'https') and parsed.netloc)
                or (url.startswith('/') and not url.startswith('//'))):
            raise ValueError(f'{config}: announcement url must be an HTTP(S) or root-relative link')
        external = parsed.scheme in ('http', 'https')
        options = ' target="_blank" rel="noopener noreferrer"' if external else ''
        link = (f'<a class="site-announcement-link" href="{html.escape(url, quote=True)}"{options}>'
                f'{html.escape(label)} <span aria-hidden="true">↗</span></a>')

    return (f'<aside class="site-announcement" aria-label="站点公告">'
            f'<div class="site-announcement-inner">'
            f'<span class="site-announcement-icon" aria-hidden="true">✳</span>'
            f'<span class="site-announcement-text">{html.escape(message.strip())}</span>'
            f'{link}</div></aside>')
