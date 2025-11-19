# utils/embed_utils.py
import discord
from datetime import datetime
from typing import List, Tuple, Optional

def create_modern_embed(
    title: Optional[str] = None,
    description: Optional[str] = None,
    color: discord.Color = discord.Color.from_rgb(88, 101, 242),  # Discord blurple
    author_name: Optional[str] = None,
    author_icon_url: Optional[str] = None,
    thumbnail_url: Optional[str] = None,
    image_url: Optional[str] = None,
    footer_text: str = "⚙️ Powered by neon.real",
    footer_icon_url: str = "https://cdn.discordapp.com/emojis/1088144557728948296.webp?size=96&quality=lossless",
    fields: Optional[List[Tuple[str, str, bool]]] = None,  # [(name, value, inline), ...]
    emoji_prefix: str = "💠"  # Small emoji prefix for titles
) -> discord.Embed:
    """
    Create a sleek, modern-style embed with consistent layout and design.
    Compatible with Python 3.12 and discord.py 2.x
    """

    embed = discord.Embed(
        title=f"{emoji_prefix} {title}" if title else None,
        description=description,
        color=color,
        timestamp=datetime.utcnow()
    )

    # Author section
    if author_name:
        embed.set_author(name=author_name, icon_url=author_icon_url or discord.Embed.Empty)

    # Optional visuals
    if thumbnail_url:
        embed.set_thumbnail(url=thumbnail_url)
    if image_url:
        embed.set_image(url=image_url)

    # Add fields if provided
    if fields:
        for name, value, inline in fields:
            embed.add_field(name=f"**{name}**", value=value, inline=inline)

    # Footer
    embed.set_footer(text=footer_text, icon_url=footer_icon_url)

    return embed
