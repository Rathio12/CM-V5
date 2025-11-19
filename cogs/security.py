import discord
from discord.ext import commands, tasks
from collections import deque, defaultdict
from datetime import datetime, timezone, timedelta
import time, json, re
from utils.storage import get_guild_settings
from utils.embed_utils import create_modern_embed

# Load config
with open("config.json", "r") as f:
    CONFIG = json.load(f)

BLOCKED_FILE_PATTERNS = [
    r"\.exe$", r"\.bat$", r"\.cmd$", r"\.dll$", r"\.sh$", r"\.js$", r"\.scr$", r"\.vbs$",
    r"\.jar$", r"\.msi$", r"\.com$", r"\.pif$", r"\.wsf$", r"\.cpl$"
]

BLACKLISTED_WORDS = [
    "malware", "virus", "trojan", "hacktool", "keygen", "crack", "cheat", "phish","discord.gg",
]

class SecurityCog(commands.Cog):
    """Security cog with fully working 1-minute timeout and logging."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.joins = defaultdict(lambda: deque())
        self.msgs = defaultdict(lambda: defaultdict(list))
        self.cleanup_cache.start()

    def cog_unload(self):
        self.cleanup_cache.cancel()

    @tasks.loop(seconds=30)
    async def cleanup_cache(self):
        cutoff = time.time() - 3600
        for guild_id, dq in list(self.joins.items()):
            while dq and dq[0] < cutoff:
                dq.popleft()
            if not dq:
                del self.joins[guild_id]

    # -----------------
    # Utilities
    # -----------------
    def _get_channel(self, guild: discord.Guild, key: str):
        settings = get_guild_settings(guild.id) or {}
        ch_id = settings.get("logging_channels", {}).get(key)
        return guild.get_channel(ch_id) if ch_id else None

    async def _send_alert(self, guild, title, description, color, emoji="⚠️"):
        if ch := self._get_channel(guild, "security-log"):
            embed = create_modern_embed(title=title, description=description, color=color, emoji_prefix=emoji)
            await ch.send(embed=embed)

    async def _notify_mods(self, guild, title, description, color):
        if ch := self._get_channel(guild, "audit-log"):
            embed = create_modern_embed(title=title, description=description, color=color, emoji_prefix="🛡️")
            await ch.send(embed=embed)

    async def _log_timeout(self, member: discord.Member, reason: str, seconds: int):
        """Send a log message for timeouts."""
        guild = member.guild
        desc = f"🕒 **Timeout Applied:** {member} — {seconds}s\n**Reason:** {reason}"
        await self._send_alert(guild, "Member Timed Out", desc, discord.Color.blue())

    async def _apply_timeout(self, member: discord.Member, reason: str, seconds: int = 60):
        """Safely apply a timeout to a member, handling permissions and roles, with logging."""
        if not isinstance(member, discord.Member):
            print(f"[SECURITY] Not a valid member: {member}")
            return

        bot_member = member.guild.me

        # Check bot permissions
        if not bot_member.guild_permissions.moderate_members:
            print(f"[SECURITY] Cannot timeout {member}: missing Moderate Members permission")
            return

        # Check role hierarchy
        if bot_member.top_role <= member.top_role:
            print(f"[SECURITY] Cannot timeout {member}: role too high")
            return

        # Calculate timeout until timestamp
        until = datetime.now(timezone.utc) + timedelta(seconds=seconds)

        # Attempt timeout
        try:
            await member.timeout(until, reason=reason)
            print(f"[SECURITY] Timed out {member} for {seconds}s: {reason}")
            # Log timeout
            await self._log_timeout(member, reason, seconds)
        except discord.Forbidden:
            print(f"[SECURITY] Cannot timeout {member}: Forbidden by Discord")
        except discord.HTTPException as e:
            print(f"[SECURITY] Failed to timeout {member}: {e}")

    # -----------------
    # Member join
    # -----------------
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild
        now = time.time()
        self.joins[guild.id].append(now)

        # Anti-raid
        raid_window = CONFIG.get("raid_window_seconds", 10)
        raid_threshold = CONFIG.get("raid_join_threshold", 5)
        recent_joins = sum(1 for t in self.joins[guild.id] if t >= now - raid_window)
        if recent_joins >= raid_threshold:
            desc = f"🚨 **Possible Raid:** {recent_joins} joins in {raid_window}s"
            await self._send_alert(guild, "Possible Raid Detected", desc, discord.Color.red())

        # Alt detection
        min_age_days = CONFIG.get("min_account_age_days", 7)
        age_days = (datetime.now(timezone.utc) - member.created_at).days
        if age_days < min_age_days:
            desc = f"⚠️ **Alt Detected:** {member} — Account age: {age_days} days"
            await self._send_alert(guild, "Alt Account Detected", desc, discord.Color.orange())

    # -----------------
    # Message events
    # -----------------
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        guild = message.guild
        now = time.time()

        # Spam detection
        history = self.msgs[guild.id][message.author.id]
        history.append(now)
        history[:] = [t for t in history if t >= now - 7]
        if len(history) > 5:
            desc = f"⚠️ **Spam detected:** {message.author} — {len(history)} messages in 7s"
            await self._send_alert(guild, "Spam Detected", desc, discord.Color.orange())
            try:
                await message.delete()
            except (discord.Forbidden, discord.NotFound):
                pass

        # Dangerous file detection
        for attach in message.attachments:
            for pattern in BLOCKED_FILE_PATTERNS:
                if re.search(pattern, attach.filename, re.IGNORECASE):
                    try:
                        await message.delete()
                        await self._apply_timeout(message.author, f"Uploaded blocked file: {attach.filename}")
                        mod_desc = f"User {message.author} uploaded blocked file `{attach.filename}` in #{message.channel.name}"
                        await self._notify_mods(guild, "Blocked File Upload", mod_desc, discord.Color.red())
                    except (discord.Forbidden, discord.NotFound):
                        pass
                    return

        # Blacklisted word detection
        if isinstance(message.content, str):
            msg_lower = message.content.lower()
            for word in BLACKLISTED_WORDS:
                if word.lower() in msg_lower:
                    try:
                        await message.delete()
                        await self._apply_timeout(message.author, f"Used blacklisted word: {word}")
                        mod_desc = f"User {message.author} used blacklisted word `{word}` in #{message.channel.name}"
                        await self._notify_mods(guild, "Blacklisted Word Detected", mod_desc, discord.Color.red())
                    except (discord.Forbidden, discord.NotFound):
                        pass
                    return

        # Allow commands to still work
        await self.bot.process_commands(message)


async def setup(bot: commands.Bot):
    await bot.add_cog(SecurityCog(bot))
