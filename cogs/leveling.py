import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import random
from utils.embed_utils import create_modern_embed

LEVEL_FILE = "data/levels.json"

# Ensure data folder exists
os.makedirs("data", exist_ok=True)
if not os.path.exists(LEVEL_FILE):
    with open(LEVEL_FILE, "w") as f:
        json.dump({}, f, indent=4)

def load_data():
    with open(LEVEL_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(LEVEL_FILE, "w") as f:
        json.dump(data, f, indent=4)

def xp_to_level(xp):
    """Calculate level from XP (curve: 100 * level^1.5)"""
    level = 0
    while xp >= int(100 * (level + 1) ** 1.5):
        xp -= int(100 * (level + 1) ** 1.5)
        level += 1
    return level

class LevelingCog(commands.Cog):
    """Leveling system with XP, progress bar, level-up messages, and leaderboard."""

    def __init__(self, bot):
        self.bot = bot
        self.level_data = load_data()

    # -------------------
    # Message listener for XP
    # -------------------
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        guild_id = str(message.guild.id)
        user_id = str(message.author.id)

        if guild_id not in self.level_data:
            self.level_data[guild_id] = {}
        if user_id not in self.level_data[guild_id]:
            self.level_data[guild_id][user_id] = {"xp": 0, "level": 0}

        # Random XP per message: 5-15 XP
        gain = random.randint(5, 15)
        self.level_data[guild_id][user_id]["xp"] += gain

        # Check level-up
        user_xp = self.level_data[guild_id][user_id]["xp"]
        current_level = self.level_data[guild_id][user_id]["level"]
        new_level = xp_to_level(user_xp)

        if new_level > current_level:
            self.level_data[guild_id][user_id]["level"] = new_level

            # Determine level-up channel
            level_ch_id = self.level_data[guild_id].get("level_channel")
            level_channel = message.guild.get_channel(level_ch_id) if level_ch_id else message.channel

            # Progress bar (full)
            next_level_xp = int(100 * (new_level + 1) ** 1.5)
            xp_for_current_level = user_xp - sum(int(100 * (i + 1) ** 1.5) for i in range(new_level))
            bar_length = 20
            filled_length = int(bar_length * xp_for_current_level / next_level_xp)
            progress_bar = "🟩" * filled_length + "⬛" * (bar_length - filled_length)

            embed = create_modern_embed(
                title=f"{message.author.display_name} leveled up!",
                description=(
                    f"🎉 {message.author.mention} reached **Level {new_level}**!\n"
                    f"XP: **{xp_for_current_level}/{next_level_xp}**\n"
                    f"`{progress_bar}`"
                ),
                color=discord.Color.green(),
                emoji_prefix="🟢"
            )
            embed.set_thumbnail(url=message.author.display_avatar.url)
            await level_channel.send(embed=embed)

        save_data(self.level_data)

    # -------------------
    # /level command
    # -------------------
    @app_commands.command(name="level", description="Check your current level and XP")
    async def level(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)

        if guild_id not in self.level_data or user_id not in self.level_data[guild_id]:
            embed = create_modern_embed(
                title="No XP Yet",
                description=f"{interaction.user.mention}, you haven't earned any XP yet. Start chatting to gain XP!",
                color=discord.Color.red(),
                emoji_prefix="⚠️"
            )
            await interaction.response.send_message(embed=embed)
            return

        data = self.level_data[guild_id][user_id]
        level = data["level"]
        xp = data["xp"]

        next_level_xp = int(100 * (level + 1) ** 1.5)
        xp_for_current_level = xp - sum(int(100 * (i + 1) ** 1.5) for i in range(level))

        # Progress bar
        bar_length = 20
        filled_length = int(bar_length * xp_for_current_level / next_level_xp)
        progress_bar = "🟩" * filled_length + "⬛" * (bar_length - filled_length)

        embed = create_modern_embed(
            title=f"{interaction.user.display_name}'s Level",
            description=(
                f"Level **{level}**\n"
                f"XP: **{xp_for_current_level}/{next_level_xp}**\n"
                f"`{progress_bar}`"
            ),
            color=discord.Color.blurple(),
            emoji_prefix="🧾"
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    # -------------------
    # /level_channel command
    # -------------------
    @app_commands.command(name="level_channel", description="Set the channel for level-up announcements")
    @app_commands.describe(channel="The text channel where level-up messages will be sent")
    @app_commands.checks.has_permissions(administrator=True)
    async def level_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        guild_id = str(interaction.guild.id)
        if guild_id not in self.level_data:
            self.level_data[guild_id] = {}

        self.level_data[guild_id]["level_channel"] = channel.id
        save_data(self.level_data)

        embed = create_modern_embed(
            title="Level Channel Set",
            description=f"✅ Level-up messages will now be sent in {channel.mention}",
            color=discord.Color.green(),
            emoji_prefix="🟢"
        )
        await interaction.response.send_message(embed=embed)

    # -------------------
    # /leaderboard command
    # -------------------
    @app_commands.command(name="leaderboard", description="Show top users by XP in this server")
    async def leaderboard(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        if guild_id not in self.level_data:
            embed = create_modern_embed(
                title="Leaderboard",
                description="No leveling data for this server.",
                color=discord.Color.red(),
                emoji_prefix="⚠️"
            )
            await interaction.response.send_message(embed=embed)
            return

        sorted_users = sorted(
            {k: v for k, v in self.level_data[guild_id].items() if isinstance(v, dict) and "xp" in v}.items(),
            key=lambda x: x[1]["xp"],
            reverse=True
        )[:10]

        description = ""
        for i, (user_id, info) in enumerate(sorted_users, start=1):
            member = interaction.guild.get_member(int(user_id))
            name = member.display_name if member else f"User ID {user_id}"
            description += f"**{i}. {name}** — Level {info['level']} | XP: {info['xp']}\n"

        embed = create_modern_embed(
            title=f"🏆 {interaction.guild.name} Leaderboard",
            description=description,
            color=discord.Color.blurple(),
            emoji_prefix="🥇"
        )
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(LevelingCog(bot))
