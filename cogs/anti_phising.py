import discord
from discord.ext import commands
import os
import json
from datetime import datetime
from utils.embed_utils import create_modern_embed

BLACKLIST_DIR = "blacklisted/"
BLOCK_LOG_FILE = "blacklisted/blocked.txt"
GUILD_DATA_DIR = "Guild_data/"

class AntiPhishing(commands.Cog):
    """Blocks blacklisted links/words and logs them to a security channel using pre-made config."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        # Ensure directories exist
        os.makedirs(BLACKLIST_DIR, exist_ok=True)
        os.makedirs(GUILD_DATA_DIR, exist_ok=True)

        # Ensure global block log exists
        if not os.path.exists(BLOCK_LOG_FILE):
            with open(BLOCK_LOG_FILE, "w", encoding="utf-8") as f:
                json.dump([], f)

        # Load all blacklisted terms
        self.blacklisted = self.load_blacklists()

    def load_blacklists(self):
        """Load all .txt files in blacklisted folder into a single list."""
        blacklist = []
        for file in os.listdir(BLACKLIST_DIR):
            if file.endswith(".txt"):
                path = os.path.join(BLACKLIST_DIR, file)
                with open(path, "r", encoding="utf-8") as f:
                    lines = [line.strip().lower() for line in f if line.strip()]
                    blacklist.extend(lines)
        print(f"[AntiPhishing] Loaded {len(blacklist)} blacklist entries.")
        return blacklist

    def save_block_log(self, user_id, guild_id, content, matched):
        """Append blocked message to blocked.txt"""
        try:
            with open(BLOCK_LOG_FILE, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except Exception:
            logs = []

        logs.append({
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "guild_id": guild_id,
            "content": content,
            "matched": matched
        })

        with open(BLOCK_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=4)

    def _get_security_channel(self, guild: discord.Guild) -> discord.TextChannel | None:
        """Fetch security-log channel from guild JSON config"""
        guild_file = os.path.join(GUILD_DATA_DIR, f"{guild.id}.json")
        if not os.path.exists(guild_file):
            return None
        with open(guild_file, "r", encoding="utf-8") as f:
            guild_data = json.load(f)
            sec_log_id = guild_data.get("logging_channels", {}).get("security-log")
            return guild.get_channel(sec_log_id) if sec_log_id else None

    async def _send_embed(self, ch: discord.TextChannel, content: str):
        """Send an embed to the given channel using your embed generator"""
        if ch:
            embed = create_modern_embed(
                title="Blocked Message Deleted",
                description=content,
                color=discord.Color.red(),
                emoji_prefix="🛡️"
            )
            await ch.send(embed=embed)

    # -------------------
    # Listen for messages
    # -------------------
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        content_lower = message.content.lower()
        matched_term = None

        for bad in self.blacklisted:
            if bad in content_lower:
                matched_term = bad
                break

        if matched_term:
            try:
                await message.delete()
            except discord.Forbidden:
                pass

            self.save_block_log(
                user_id=message.author.id,
                guild_id=message.guild.id,
                content=message.content,
                matched=matched_term
            )

            # Fetch the security log channel dynamically
            sec_ch = self._get_security_channel(message.guild)
            if sec_ch:
                description = (
                    f"🚫 **User:** {message.author.mention} (`{message.author.id}`)\n"
                    f"💬 **Message:** {message.content}\n"
                    f"⚠️ **Matched:** `{matched_term}`"
                )
                await self._send_embed(sec_ch, description)


async def setup(bot: commands.Bot):
    await bot.add_cog(AntiPhishing(bot))
