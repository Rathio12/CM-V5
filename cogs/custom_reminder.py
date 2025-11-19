import discord
from discord import app_commands
from discord.ext import commands, tasks
from utils.storage import get_guild_settings, set_guild_settings
from datetime import datetime, timezone

class SimpleReminder(commands.Cog):
    """Daily text reminders."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.daily_reminder_loop.start()

    @app_commands.command(
        name="set_reminder",
        description="Set a daily reminder with a title and message"
    )
    @app_commands.describe(
        hour="Hour in 24h format (UTC)",
        minute="Minute (UTC)",
        title="Title of the reminder",
        message="Message of the reminder"
    )
    async def set_reminder(
        self,
        interaction: discord.Interaction,
        hour: int,
        minute: int,
        title: str,
        message: str
    ):
        if not (0 <= hour < 24) or not (0 <= minute < 60):
            return await interaction.response.send_message("❌ Invalid time.", ephemeral=True)

        settings = get_guild_settings(interaction.guild.id)
        reminders = settings.get("daily_reminders", [])
        reminders.append({
            "channel_id": interaction.channel.id,
            "hour": hour,
            "minute": minute,
            "title": title,
            "message": message,
            "last_sent": None
        })
        settings["daily_reminders"] = reminders
        set_guild_settings(interaction.guild.id, settings)

        await interaction.response.send_message(
            f"✅ Daily reminder set for **{hour:02d}:{minute:02d} UTC** in {interaction.channel.mention}.",
            ephemeral=True
        )

    @tasks.loop(seconds=30)
    async def daily_reminder_loop(self):
        now = datetime.now(timezone.utc)
        today_str = now.date().isoformat()

        for guild in self.bot.guilds:
            settings = get_guild_settings(guild.id)
            reminders = settings.get("daily_reminders", [])

            for reminder in reminders:
                if reminder.get("last_sent") == today_str:
                    continue
                if reminder["hour"] == now.hour and reminder["minute"] == now.minute:
                    channel = guild.get_channel(reminder["channel_id"])
                    if channel:
                        try:
                            await channel.send(f"**{reminder['title']}**\n{reminder['message']}")
                            reminder["last_sent"] = today_str
                            settings["daily_reminders"] = reminders
                            set_guild_settings(guild.id, settings)
                        except discord.Forbidden:
                            continue

    @daily_reminder_loop.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()

async def setup(bot: commands.Bot):
    await bot.add_cog(SimpleReminder(bot))
