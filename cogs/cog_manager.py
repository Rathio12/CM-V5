import discord
from discord import app_commands
from discord.ext import commands
from utils.storage import get_disabled_cogs, enable_cog_for_guild, disable_cog_for_guild
from utils.embed_utils import create_modern_embed

BOT_OWNER_ID = 1305579806557208657  # Replace with your Discord ID
CORE_COGS = ["CogManager", "LoggingCog", "SetupCog", "GuildJoin", "WelcomeCog"]  # Core cogs

class CogManager(commands.Cog):
    """Enable, disable, and list cogs per guild with core cogs protected."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _all_cogs(self):
        return list(self.bot.cogs.keys())

    async def _notify_owner(self, message: str):
        owner = self.bot.get_user(BOT_OWNER_ID)
        if owner:
            try:
                await owner.send(message)
            except discord.Forbidden:
                print("Cannot DM the bot owner.")

    async def _notify_guild_owner(self, guild_owner: discord.User, message: str):
        if guild_owner:
            try:
                await guild_owner.send(message)
            except discord.Forbidden:
                print(f"Cannot DM server owner {guild_owner}.")

    # -------------------
    # Disable a cog
    # -------------------
    @commands.hybrid_command(name="cog-disable", description="Disable a cog for this server")
    @app_commands.describe(cog_name="The cog to disable")
    @app_commands.checks.has_permissions(administrator=True)
    async def disable_cog_command(self, ctx: commands.Context, *, cog_name: str):
        interaction = ctx.interaction
        all_cogs = self._all_cogs()

        if cog_name not in all_cogs:
            await ctx.send(f"❌ Unknown cog: `{cog_name}`", ephemeral=True)
            return

        if cog_name in CORE_COGS:
            await ctx.send(f"⛔ Core cog `{cog_name}` cannot be disabled.", ephemeral=True)

            # Notify bot owner
            await self._notify_owner(
                f"User {ctx.author} ({ctx.author.id}) tried to disable core cog `{cog_name}` "
                f"in guild {ctx.guild.name} ({ctx.guild.id})."
            )

            # Notify guild owner
            guild_owner = ctx.guild.owner
            if guild_owner:
                await self._notify_guild_owner(
                    guild_owner,
                    f"Hi {guild_owner.name}, you tried to disable core cog `{cog_name}` "
                    f"in your server `{ctx.guild.name}`. This cog is protected."
                )
            return

        disabled = get_disabled_cogs(ctx.guild.id)
        if cog_name in disabled:
            await ctx.send(f"ℹ️ Cog `{cog_name}` is already disabled.", ephemeral=True)
            return

        disable_cog_for_guild(ctx.guild.id, cog_name)
        embed = create_modern_embed(
            title="Cog Disabled",
            description=f"⛔ Cog `{cog_name}` has been disabled for this server.",
            color=discord.Color.red(),
            emoji_prefix="⚙️"
        )
        await ctx.send(embed=embed, ephemeral=True)

    # -------------------
    # Enable a cog
    # -------------------
    @commands.hybrid_command(name="cog-enable", description="Enable a cog for this server")
    @app_commands.describe(cog_name="The cog to enable")
    @app_commands.checks.has_permissions(administrator=True)
    async def enable_cog_command(self, ctx: commands.Context, *, cog_name: str):
        all_cogs = self._all_cogs()

        if cog_name not in all_cogs:
            await ctx.send(f"❌ Unknown cog: `{cog_name}`", ephemeral=True)
            return

        disabled = get_disabled_cogs(ctx.guild.id)
        if cog_name not in disabled:
            await ctx.send(f"ℹ️ Cog `{cog_name}` is already enabled.", ephemeral=True)
            return

        enable_cog_for_guild(ctx.guild.id, cog_name)
        embed = create_modern_embed(
            title="Cog Enabled",
            description=f"✅ Cog `{cog_name}` has been enabled for this server.",
            color=discord.Color.green(),
            emoji_prefix="⚙️"
        )
        await ctx.send(embed=embed, ephemeral=True)

    # -------------------
    # List all cogs
    # -------------------
    @commands.hybrid_command(name="cog-list", description="List all cogs and disabled cogs for this server")
    async def list_cogs(self, ctx: commands.Context):
        all_cogs = self._all_cogs()
        disabled = get_disabled_cogs(ctx.guild.id)

        lines = []
        for cog in all_cogs:
            if cog in disabled:
                lines.append(f"⛔ {cog}")
            else:
                lines.append(f"✅ {cog}")

        embed = create_modern_embed(
            title="Server Cogs",
            description="\n".join(lines) if lines else "No cogs loaded.",
            color=discord.Color.blurple(),
            emoji_prefix="ℹ️"
        )
        await ctx.send(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(CogManager(bot))
