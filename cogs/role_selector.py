import discord
import os
import json
from discord.ext import commands
from discord import app_commands
from utils.embed_utils import create_modern_embed

# -------------------------
# Data Storage
# -------------------------
BASE_DIR = "data/guilds/roles/"
os.makedirs(BASE_DIR, exist_ok=True)

def guild_file(gid: int):
    return f"{BASE_DIR}/{gid}.json"

def load_roles(gid: int):
    path = guild_file(gid)
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return json.load(f)

def save_roles(gid: int, data: list):
    with open(guild_file(gid), "w") as f:
        json.dump(data, f, indent=4)

# -----------------------------
# Role Select Menu
# -----------------------------
class RoleSelectorMenu(discord.ui.Select):
    def __init__(self, guild: discord.Guild):
        self.guild = guild
        roles = load_roles(guild.id)
        options = []
        for rid in roles:
            role = guild.get_role(rid)
            if role:
                options.append(discord.SelectOption(label=role.name, value=str(role.id)))

        super().__init__(
            custom_id=f"roleselect::{guild.id}",
            placeholder="Select your roles…",
            min_values=0,
            max_values=len(options),
            options=options
        )
        self.all_role_ids = [int(o.value) for o in options]

    async def callback(self, interaction: discord.Interaction):
        member = interaction.user
        chosen = [int(v) for v in self.values]

        # Remove all roles from this selector
        for rid in self.all_role_ids:
            role = interaction.guild.get_role(rid)
            if role and role in member.roles:
                await member.remove_roles(role)

        # Add selected roles
        for rid in chosen:
            role = interaction.guild.get_role(rid)
            if role:
                await member.add_roles(role)

        embed = create_modern_embed(
            title="Roles Updated",
            description="Your roles have been updated! ✅"
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

# -----------------------------
# Persistent View
# -----------------------------
class RoleSelectorView(discord.ui.View):
    def __init__(self, bot, guild: discord.Guild):
        super().__init__(timeout=None)
        self.add_item(RoleSelectorMenu(guild))
        bot.add_view(self)  # persistent view

# -----------------------------
# Cog
# -----------------------------
class RoleSelector(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        # Load persistent views for all guilds
        for guild in self.bot.guilds:
            if load_roles(guild.id):
                RoleSelectorView(self.bot, guild)
        print("Persistent role selector loaded for all guilds.")

    # -----------------------------
    # Add Role
    # -----------------------------
    @app_commands.command(name="roleselect_add", description="Add a role to the selector")
    @app_commands.checks.has_permissions(administrator=True)
    async def add_role(self, interaction: discord.Interaction, role: discord.Role):
        roles = load_roles(interaction.guild_id)
        if role.id not in roles:
            roles.append(role.id)
            save_roles(interaction.guild_id, roles)

        embed = create_modern_embed(
            title="Role Added",
            description=f"Added <@&{role.id}> to the selector."
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # -----------------------------
    # Remove Role
    # -----------------------------
    @app_commands.command(name="roleselect_remove", description="Remove a role from the selector")
    @app_commands.checks.has_permissions(administrator=True)
    async def remove_role(self, interaction: discord.Interaction, role: discord.Role):
        roles = load_roles(interaction.guild_id)
        if role.id in roles:
            roles.remove(role.id)
            save_roles(interaction.guild_id, roles)

        embed = create_modern_embed(
            title="Role Removed",
            description=f"Removed <@&{role.id}> from the selector."
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # -----------------------------
    # Send Panel
    # -----------------------------
    @app_commands.command(name="roleselect_panel", description="Send the role selection panel")
    @app_commands.checks.has_permissions(administrator=True)
    async def send_panel(self, interaction: discord.Interaction):
        embed = create_modern_embed(
            title="Role Selector",
            description="Select your roles from the dropdown below!"
        )
        view = RoleSelectorView(self.bot, interaction.guild)
        await interaction.response.send_message(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(RoleSelector(bot))
