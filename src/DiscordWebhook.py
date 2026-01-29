"""Minimal helper to send Discord notifications during training."""

import os
from typing import Optional

from discord_webhook import DiscordEmbed, DiscordWebhook

DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1466510737009803420/SPhFts6q0B_fac2FYEdHrEzmFIRAkZcYvZmKFy8-FmlLUN7-p0AJGZqOMEwOHK8Uy6mP"

def _resolve_webhook_url(webhook_url: Optional[str]) -> str:
    return (webhook_url or DISCORD_WEBHOOK_URL).strip()


def post_text(message: str, webhook_url: Optional[str] = None, username: str = "QB-PIER") -> None:
    """Post a plain text message to Discord."""
    resolved_url = _resolve_webhook_url(webhook_url)
    if not resolved_url:
        return

    webhook = DiscordWebhook(url=resolved_url, username=username, content=message)
    try:
        webhook.execute()
    except Exception:
        # The logger should never break training, so ignore webhook errors.
        pass

def post_image_with_caption(
    image_path: str,
    caption: str,
    webhook_url: Optional[str] = None,
    username: str = "QB-PIER",
) -> None:
    """Post an image file with a caption to Discord."""
    resolved_url = _resolve_webhook_url(webhook_url)
    if not resolved_url or not image_path or not os.path.exists(image_path):
        return

    webhook = DiscordWebhook(url=resolved_url, username=username)
    embed = DiscordEmbed(description=caption)
    webhook.add_embed(embed)

    with open(image_path, "rb") as file_data:
        webhook.add_file(file=file_data.read(), filename=os.path.basename(image_path))

    try:
        webhook.execute()
    except Exception:
        # The logger should never break training, so ignore webhook errors.
        pass
