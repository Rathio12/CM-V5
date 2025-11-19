import discord
from discord.ext import commands
from utils.storage import get_guild_settings
from utils.embed_utils import create_modern_embed

# Replace with your support/main guild ID and channel ID
MAIN_GUILD_ID = 1313834110581739622  # your support guild
MAIN_CHANNEL_ID = 1438634810867318805  # the channel in support guild to log new joins

class GuildJoinLogCog(commands.Cog):
    """Logs when the bot joins a new server with invite and server info."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        # Try to create an invite in the joined guild
        target_channel = guild.system_channel or next(
            (c for c in guild.text_channels if c.permissions_for(guild.me).create_instant_invite),
            None
        )
        invite_url = "No invite could be created"
        if target_channel:
            try:
                invite = await target_channel.create_invite(
                    max_age=0, max_uses=0, unique=True, reason="New guild join log"
                )
                invite_url = invite.url
            except discord.Forbidden:
                invite_url = "Could not create invite"

        # Info about the new guild
        owner = guild.owner or "Unknown"
        owner_id = getattr(guild.owner, "id", "Unknown")
        desc = (
            f"🤖 **Bot added to server:** {guild.name} (ID: {guild.id})\n"
            f"👑 **Owner:** {owner} (ID: {owner_id})\n"
            f"📢 **Invite:** {invite_url}"
        )

        embed = create_modern_embed(
            title="New Guild Joined",
            description=desc,
            color=discord.Color.green(),
            emoji_prefix="🟢"
        )

        # Send to the join-log channel configured in the guild itself (if any)
        settings = get_guild_settings(guild.id) or {}
        log_ch_id = settings.get("logging_channels", {}).get("join-log")
        if log_ch_id:
            log_channel = guild.get_channel(log_ch_id)
            if log_channel:
                await log_channel.send(embed=embed)

        # Send to main support guild channel
        main_guild = self.bot.get_guild(MAIN_GUILD_ID)
        if main_guild:
            main_ch = main_guild.get_channel(MAIN_CHANNEL_ID)
            if main_ch:
                await main_ch.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(GuildJoinLogCog(bot))
