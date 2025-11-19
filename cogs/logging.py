import discord
from discord.ext import commands
from utils.storage import get_guild_settings
from utils.embed_utils import create_modern_embed

class LoggingCog(commands.Cog):
    """Fully functional logging cog covering moderation, audit, join/leave, raid, security, bulk deletes, stickers, guild updates, and voice state."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _get_channel(self, guild: discord.Guild, key: str) -> discord.TextChannel | None:
        """Retrieve the pre-configured logging channel."""
        settings = get_guild_settings(guild.id) or {}
        ch_id = settings.get("logging_channels", {}).get(key)
        return guild.get_channel(ch_id) if ch_id else None

    async def _send_embed(self, ch: discord.TextChannel, title: str, description: str, color: discord.Color, emoji: str = "ℹ️"):
        if ch:
            embed = create_modern_embed(title=title, description=description, color=color, emoji_prefix=emoji)
            await ch.send(embed=embed)

    # -------------------
    # Member events
    # -------------------
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        ch = self._get_channel(member.guild, "join-log")
        if ch:
            desc = f"**Member Joined:** {member.mention} (ID: {member.id})"
            await self._send_embed(ch, "Member Joined", desc, discord.Color.green(), "🟢")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        ch = self._get_channel(member.guild, "join-log")
        if ch:
            desc = f"**Member Left:** {member.mention} (ID: {member.id})"
            await self._send_embed(ch, "Member Left", desc, discord.Color.red(), "🔴")

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        ch = self._get_channel(guild, "mod-log")
        if ch:
            desc = f"**User Banned:** {user} (ID: {user.id})"
            await self._send_embed(ch, "Member Banned", desc, discord.Color.red(), "⛔")

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        ch = self._get_channel(guild, "mod-log")
        if ch:
            desc = f"**User Unbanned:** {user} (ID: {user.id})"
            await self._send_embed(ch, "Member Unbanned", desc, discord.Color.green(), "✅")

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        ch = self._get_channel(before.guild, "audit-log")
        if not ch:
            return
        changes = []
        if before.nick != after.nick:
            changes.append(f"Nickname: `{before.nick}` → `{after.nick}`")
        if before.roles != after.roles:
            before_roles = ", ".join(r.name for r in before.roles[1:])
            after_roles = ", ".join(r.name for r in after.roles[1:])
            changes.append(f"Roles: {before_roles} → {after_roles}")
        if before.avatar != after.avatar:
            changes.append("Avatar changed")
        if before.display_name != after.display_name:
            changes.append(f"Display Name: `{before.display_name}` → `{after.display_name}`")
        if changes:
            desc = "\n".join(changes)
            await self._send_embed(ch, f"Member Updated: {after}", desc, discord.Color.orange(), "🟠")

    # -------------------
    # Role events
    # -------------------
    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role):
        ch = self._get_channel(role.guild, "audit-log")
        if ch:
            desc = f"**Role Created:** {role.name} (ID: {role.id})"
            await self._send_embed(ch, "Role Created", desc, discord.Color.green(), "🟢")

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        ch = self._get_channel(role.guild, "audit-log")
        if ch:
            desc = f"**Role Deleted:** {role.name} (ID: {role.id})"
            await self._send_embed(ch, "Role Deleted", desc, discord.Color.red(), "🔴")

    @commands.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        ch = self._get_channel(before.guild, "audit-log")
        if ch:
            changes = []
            if before.name != after.name:
                changes.append(f"Name: `{before.name}` → `{after.name}`")
            if before.permissions != after.permissions:
                changes.append("Permissions changed")
            if changes:
                desc = "\n".join(changes)
                await self._send_embed(ch, "Role Updated", desc, discord.Color.orange(), "🟠")

    # -------------------
    # Channel events
    # -------------------
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        ch = self._get_channel(channel.guild, "audit-log")
        if ch:
            desc = f"**Channel Created:** {channel.name} (ID: {channel.id})"
            await self._send_embed(ch, "Channel Created", desc, discord.Color.green(), "🟢")

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        ch = self._get_channel(channel.guild, "audit-log")
        if ch:
            desc = f"**Channel Deleted:** {channel.name} (ID: {channel.id})"
            await self._send_embed(ch, "Channel Deleted", desc, discord.Color.red(), "🔴")

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        ch = self._get_channel(before.guild, "audit-log")
        if ch:
            changes = []
            if before.name != after.name:
                changes.append(f"Name: `{before.name}` → `{after.name}`")
            if hasattr(before, "topic") and getattr(before, "topic", None) != getattr(after, "topic", None):
                changes.append(f"Topic changed: `{before.topic}` → `{after.topic}`")
            if changes:
                desc = "\n".join(changes)
                await self._send_embed(ch, "Channel Updated", desc, discord.Color.orange(), "🟠")

    # -------------------
    # Emoji events
    # -------------------
    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild: discord.Guild, before, after):
        ch = self._get_channel(guild, "audit-log")
        if ch:
            desc = f"**Emoji Update:**\nBefore: {[e.name for e in before]}\nAfter: {[e.name for e in after]}"
            await self._send_embed(ch, "Emoji Updated", desc, discord.Color.orange(), "🟠")

    # -------------------
    # Message events
    # -------------------
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot:
            return
        ch = self._get_channel(message.guild, "audit-log")
        if ch:
            desc = f"**Message Deleted:** {message.author.mention}\nContent: {message.content}"
            await self._send_embed(ch, "Message Deleted", desc, discord.Color.red(), "🟥")

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if before.author.bot or before.content == after.content:
            return
        ch = self._get_channel(before.guild, "audit-log")
        if ch:
            desc = f"**Message Edited:** {before.author.mention}\nBefore: {before.content}\nAfter: {after.content}"
            await self._send_embed(ch, "Message Edited", desc, discord.Color.orange(), "🟠")

    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages):
        if not messages:
            return
        ch = self._get_channel(messages[0].guild, "bulk-delete-log")
        if ch:
            desc = f"**Bulk Messages Deleted:** {len(messages)} messages"
            await self._send_embed(ch, "Bulk Delete", desc, discord.Color.red(), "🟥")

    # -------------------
    # Sticker events
    # -------------------
    @commands.Cog.listener()
    async def on_guild_sticker_create(self, sticker: discord.Sticker):
        ch = self._get_channel(sticker.guild, "sticker-log")
        if ch:
            desc = f"**Sticker Created:** {sticker.name} (ID: {sticker.id})"
            await self._send_embed(ch, "Sticker Created", desc, discord.Color.green(), "🟢")

    @commands.Cog.listener()
    async def on_guild_sticker_delete(self, sticker: discord.Sticker):
        ch = self._get_channel(sticker.guild, "sticker-log")
        if ch:
            desc = f"**Sticker Deleted:** {sticker.name} (ID: {sticker.id})"
            await self._send_embed(ch, "Sticker Deleted", desc, discord.Color.red(), "🔴")

    @commands.Cog.listener()
    async def on_guild_sticker_update(self, before: discord.Sticker, after: discord.Sticker):
        ch = self._get_channel(before.guild, "sticker-log")
        if ch:
            changes = []
            if before.name != after.name:
                changes.append(f"Name: `{before.name}` → `{after.name}`")
            if changes:
                desc = "\n".join(changes)
                await self._send_embed(ch, "Sticker Updated", desc, discord.Color.orange(), "🟠")

    # -------------------
    # Guild updates
    # -------------------
    @commands.Cog.listener()
    async def on_guild_update(self, before: discord.Guild, after: discord.Guild):
        ch = self._get_channel(before, "guild-log")
        if ch:
            changes = []
            if before.name != after.name:
                changes.append(f"Name: `{before.name}` → `{after.name}`")
            if before.icon != after.icon:
                changes.append("Icon changed")
            if before.afk_channel != after.afk_channel:
                changes.append(f"AFK Channel changed: {before.afk_channel} → {after.afk_channel}")
            if changes:
                desc = "\n".join(changes)
                await self._send_embed(ch, "Guild Updated", desc, discord.Color.orange(), "🟠")

    # -------------------
    # Voice state events
    # -------------------
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        ch = self._get_channel(member.guild, "voice-log")
        if not ch:
            return
        changes = []
        if before.channel != after.channel:
            changes.append(f"Moved: `{before.channel}` → `{after.channel}`")
        if before.self_mute != after.self_mute:
            changes.append(f"Self Mute: `{before.self_mute}` → `{after.self_mute}`")
        if before.self_deaf != after.self_deaf:
            changes.append(f"Self Deaf: `{before.self_deaf}` → `{after.self_deaf}`")
        if before.mute != after.mute:
            changes.append(f"Server Mute: `{before.mute}` → `{after.mute}`")
        if before.deaf != after.deaf:
            changes.append(f"Server Deaf: `{before.deaf}` → `{after.deaf}`")
        if changes:
            desc = "\n".join(changes)
            await self._send_embed(ch, f"Voice State Update: {member}", desc, discord.Color.orange(), "🎙️")


async def setup(bot: commands.Bot):
    await bot.add_cog(LoggingCog(bot))
