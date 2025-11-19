import discord
from discord import app_commands
from discord.ext import commands
import os
import json
from utils.embed_utils import create_modern_embed
from utils.storage import get_guild_settings

AUTO_ROLE_FILE = "data/autorole.json"
os.makedirs("data", exist_ok=True)

def load_data():
    if not os.path.exists(AUTO_ROLE_FILE):
        return {}
    with open(AUTO_ROLE_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(AUTO_ROLE_FILE, "w") as f:
        json.dump(data, f, indent=4)

class AutoRoleCog(commands.Cog):
    """Automatically assign a role to new members with logging."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.data = load_data()

    # -------------------
    # Slash command to setup autorole
    # -------------------
    @app_commands.command(
        name="autorole_setup",
        description="Set the role to automatically give new members"
    )
    @app_commands.describe(role="Role to assign automatically")
    @app_commands.checks.has_permissions(administrator=True)
    async def autorole_setup(self, interaction: discord.Interaction, role: discord.Role):
        guild_id = str(interaction.guild.id)
        self.data[guild_id] = role.id
        save_data(self.data)
        await interaction.response.send_message(
            f"✅ Auto-role set to {role.mention} for new members.", ephemeral=True
        )

    # -------------------
    # Listener for member join
    # -------------------
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild_id = str(member.guild.id)
        role_id = self.data.get(guild_id)
        if not role_id:
            return

        role = member.guild.get_role(role_id)
        if role:
            try:
                await member.add_roles(role, reason="Auto-role for new member")
            except discord.Forbidden:
                print(f"Cannot assign role {role.name} in guild {member.guild.name}.")
                return

            # Send log to audit-log channel if configured
            settings = get_guild_settings(member.guild.id) or {}
            log_ch_id = settings.get("logging_channels", {}).get("audit-log")
            log_channel = member.guild.get_channel(log_ch_id) if log_ch_id else None

            if log_channel:
                embed = create_modern_embed(
                    title="Auto-role Assigned",
                    description=f"🛡️ {member.mention} has been given the role **{role.name}**.",
                    color=discord.Color.green(),
                    emoji_prefix="✅"
                )
                await log_channel.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(AutoRoleCog(bot))
