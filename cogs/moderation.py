import discord
from discord import app_commands
from discord.ext import commands
from utils.storage import get_guild_settings
from utils.embed_utils import create_modern_embed

class ModerationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _log(self, guild, key):
        data = get_guild_settings(guild.id)
        ch_id = data.get("logging_channels", {}).get(key)
        return guild.get_channel(ch_id) if ch_id else None

    async def _send_mod_embed(self, guild, title, description, color, emoji="⚠️"):
        embed = create_modern_embed(title=title, description=description, color=color, emoji_prefix=emoji)
        if (ch := self._log(guild, "mod-log")):
            await ch.send(embed=embed)
        return embed

    @app_commands.command(name="ban", description="Ban a member (Admin only)")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        await member.ban(reason=reason)
        description = f"**User:** {member.mention}\n**Moderator:** {interaction.user.mention}\n**Reason:** {reason}"
        embed = await self._send_mod_embed(interaction.guild, "Member Banned", description, discord.Color.red(), "⛔")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="kick", description="Kick a member (Admin only)")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        await member.kick(reason=reason)
        description = f"**User:** {member.mention}\n**Moderator:** {interaction.user.mention}\n**Reason:** {reason}"
        embed = await self._send_mod_embed(interaction.guild, "Member Kicked", description, discord.Color.orange(), "⚠️")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="softban", description="Softban a member (Admin only)")
    @app_commands.checks.has_permissions(ban_members=True)
    async def softban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        await interaction.guild.ban(member, reason=reason)
        await interaction.guild.unban(member)
        description = f"**User:** {member.mention}\n**Moderator:** {interaction.user.mention}\n**Reason:** {reason}"
        embed = await self._send_mod_embed(interaction.guild, "Member Softbanned", description, discord.Color.red(), "🚫")
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(ModerationCog(bot))
