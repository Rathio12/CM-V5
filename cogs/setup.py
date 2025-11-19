import discord
from discord import app_commands
from discord.ext import commands
from utils.storage import get_guild_settings, set_guild_settings
from utils.embed_utils import create_modern_embed

# All logging types
LOG_TYPES = [
    "mod-log", "audit-log", "join-log", "raid-log",
    "security-log", "bulk-delete-log", "sticker-log",
    "guild-log", "voice-log"
]

# -------------------
# Manual Setup: select log type & mention channel
# -------------------
class LogTypeDropdown(discord.ui.Select):
    def __init__(self, guild: discord.Guild):
        self.guild = guild
        options = [
            discord.SelectOption(label="Moderation Log", value="mod-log"),
            discord.SelectOption(label="Audit Log", value="audit-log"),
            discord.SelectOption(label="Join/Leave Log", value="join-log"),
            discord.SelectOption(label="Raid Log", value="raid-log"),
            discord.SelectOption(label="Security Log", value="security-log"),
            discord.SelectOption(label="Bulk Delete Log", value="bulk-delete-log"),
            discord.SelectOption(label="Sticker Log", value="sticker-log"),
            discord.SelectOption(label="Guild Update Log", value="guild-log"),
            discord.SelectOption(label="Voice State Log", value="voice-log")
        ]
        super().__init__(placeholder="Select log type to configure", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        log_type = self.values[0]

        # Send instructions to type/mention the channel
        embed = create_modern_embed(
            title=f"Configure {log_type}",
            description=f"Please **mention the channel** where `{log_type}` should be logged.\nExample: `#mod-chat`",
            color=discord.Color.blurple(),
            emoji_prefix="🛠️"
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

        def check(m: discord.Message):
            return (
                m.author == interaction.user
                and m.channel == interaction.channel
                and len(m.channel_mentions) > 0
            )

        try:
            msg = await interaction.client.wait_for("message", check=check, timeout=120)
        except:
            await interaction.followup.send("❌ Timeout: You did not mention a channel in time.", ephemeral=True)
            return

        ch = msg.channel_mentions[0]

        # Save to JSON
        settings = get_guild_settings(interaction.guild.id)
        logging_channels = settings.get("logging_channels", {})
        logging_channels[log_type] = ch.id
        settings["logging_channels"] = logging_channels
        set_guild_settings(interaction.guild.id, settings)

        # Confirmation
        confirm_embed = create_modern_embed(
            title=f"{log_type} Setup Complete",
            description=f"✅ Channel {ch.mention} has been set for `{log_type}`.",
            color=discord.Color.green(),
            emoji_prefix="🛠️"
        )
        await interaction.followup.send(embed=confirm_embed, ephemeral=True)


class SetupView(discord.ui.View):
    def __init__(self, guild: discord.Guild):
        super().__init__(timeout=None)
        self.add_item(LogTypeDropdown(guild))


# -------------------
# Cog
# -------------------
class SetupCog(commands.Cog):
    """Setup logging channels manually or automatically."""

    def __init__(self, bot):
        self.bot = bot

    # -------------------
    # Manual setup
    # -------------------
    @app_commands.command(
        name="setup",
        description="Setup logging channels manually by mentioning a channel"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def setup(self, interaction: discord.Interaction):
        view = SetupView(interaction.guild)
        embed = create_modern_embed(
            title="Logging Setup",
            description=(
                "Step 1: Select the type of logging channel to configure.\n"
                "Step 2: After selecting, **mention the channel** in chat where logs should go.\n\n"
                "You can configure Moderation, Audit, Join/Leave, Raid, Security, Bulk Deletes, "
                "Stickers, Guild Updates, and Voice State logs."
            ),
            color=discord.Color.blurple(),
            emoji_prefix="🛠️"
        )
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    # -------------------
    # Automatic setup
    # -------------------
    @app_commands.command(
        name="setup_auto",
        description="Automatically create a category and logging channels"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_auto(self, interaction: discord.Interaction):
        guild = interaction.guild
        settings = get_guild_settings(guild.id)
        logging_channels = settings.get("logging_channels", {})

        # Defer interaction to avoid timeout
        await interaction.response.defer(ephemeral=True)

        # Create category with restricted @everyone permissions
        category_name = "Server Logs"
        category = discord.utils.get(guild.categories, name=category_name)
        if not category:
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True)
            }
            category = await guild.create_category(category_name, overwrites=overwrites)

        created_channels = []
        for log_type in LOG_TYPES:
            if log_type in logging_channels and guild.get_channel(logging_channels[log_type]):
                continue
            channel_name = log_type.replace("-", "_")
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True)
            }
            channel = await guild.create_text_channel(channel_name, category=category, overwrites=overwrites)
            logging_channels[log_type] = channel.id
            created_channels.append(channel.name)

        settings["logging_channels"] = logging_channels
        set_guild_settings(guild.id, settings)

        # Confirmation
        embed = create_modern_embed(
            title="Automatic Setup Complete",
            description=(
                f"✅ Logging category `{category.name}` created.\n"
                f"✅ Channels created: {', '.join(created_channels) if created_channels else 'None, all channels existed'}"
            ),
            color=discord.Color.green(),
            emoji_prefix="🛠️"
        )
        await interaction.followup.send(embed=embed, ephemeral=True)


# -------------------
# Add cog
# -------------------
async def setup(bot: commands.Bot):
    await bot.add_cog(SetupCog(bot))
