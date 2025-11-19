import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from utils.embed_utils import create_modern_embed

DATA_FOLDER = "data/guilds"
os.makedirs(DATA_FOLDER, exist_ok=True)

def get_guild_file(guild_id: int):
    return os.path.join(DATA_FOLDER, f"{guild_id}.json")

def load_guild_data(guild_id: int):
    path = get_guild_file(guild_id)
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)

def save_guild_data(guild_id: int, data: dict):
    path = get_guild_file(guild_id)
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

class JoinLeaveCog(commands.Cog):
    """Join/Leave logging with persistent guild config and clean embeds."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # -------------------
    # Member Join
    # -------------------
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild_id = member.guild.id
        data = load_guild_data(guild_id)
        channel_id = data.get("joinleave_channel")
        if not channel_id:
            return  # Channel not configured

        ch = member.guild.get_channel(channel_id)
        if not ch:
            return

        embed = create_modern_embed(
            title=None,
            description=f"👋 {member.mention} joined the server",
            color=discord.Color.green()
        )
        await ch.send(embed=embed)

    # -------------------
    # Member Leave
    # -------------------
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        guild_id = member.guild.id
        data = load_guild_data(guild_id)
        channel_id = data.get("joinleave_channel")
        if not channel_id:
            return

        ch = member.guild.get_channel(channel_id)
        if not ch:
            return

        embed = create_modern_embed(
            title=None,
            description=f"👋 {member.display_name} left the server",
            color=discord.Color.red()
        )
        await ch.send(embed=embed)

    # -------------------
    # /joinleave_setup command
    # -------------------
    @app_commands.command(name="joinleave_setup", description="Setup the channel for join/leave messages")
    @app_commands.describe(channel="Select the text channel for join/leave messages")
    @app_commands.checks.has_permissions(administrator=True)
    async def joinleave_setup(self, interaction: discord.Interaction, channel: discord.TextChannel):
        data = load_guild_data(interaction.guild.id)
        data["joinleave_channel"] = channel.id
        save_guild_data(interaction.guild.id, data)

        embed = create_modern_embed(
            title="Join/Leave Channel Configured",
            description=f"✅ Join/Leave messages will now be sent in {channel.mention}",
            color=discord.Color.green(),
            emoji_prefix="🛠️"
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(JoinLeaveCog(bot))
