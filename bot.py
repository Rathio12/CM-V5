import os
import logging
from datetime import datetime, timezone

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv  # pip install python-dotenv

from utils.storage import get_guild_settings
from utils.embed_utils import create_modern_embed

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("CM-V5.4")

# -------------------
# Load environment variables
# -------------------
load_dotenv()  # loads .env file if present
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise SystemExit("DISCORD_TOKEN not set in environment variables.")

PREFIX = os.getenv("BOT_PREFIX", "?")

# -------------------
# Bot setup
# -------------------
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# Track bot start time (timezone-aware UTC)
START_TIME = datetime.now(timezone.utc)

# -------------------
# Rich Presence Task
# -------------------
@tasks.loop(seconds=30)
async def update_status():
    total_members = sum(guild.member_count for guild in bot.guilds)
    uptime_delta = datetime.now(timezone.utc) - START_TIME

    days, remainder = divmod(int(uptime_delta.total_seconds()), 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, _ = divmod(remainder, 60)
    uptime_str = f"{days}d {hours}h {minutes}m" if days > 0 else f"{hours}h {minutes}m"

    activity = discord.Activity(
        type=discord.ActivityType.watching,
        name=f"{total_members} users | Uptime {uptime_str}"
    )
    await bot.change_presence(activity=activity)

# -------------------
# Cog Loader
# -------------------
async def load_cogs():
    for file in os.listdir("./cogs"):
        if file.endswith(".py"):
            try:
                await bot.load_extension(f"cogs.{file[:-3]}")
                log.info(f"✅ Loaded cog: {file}")
            except Exception as e:
                log.error(f"❌ Failed to load {file}: {e}")

# -------------------
# Events
# -------------------
@bot.event
async def setup_hook():
    await load_cogs()

@bot.event
async def on_ready():
    log.info(f"Logged in as {bot.user}")

    # Start rich presence
    update_status.start()

    # Send startup embed to configured channel if exists
    for guild in bot.guilds:
        settings = get_guild_settings(guild.id)
        config_ch_id = settings.get("config_channel")
        config_ch = guild.get_channel(config_ch_id) if config_ch_id else None

        if config_ch:
            embed = create_modern_embed(
                title="Bot Ready",
                description=f"Guild ID: {guild.id}\nAll settings loaded successfully.",
                color=discord.Color.green(),
                emoji_prefix="⚙️"
            )
            await config_ch.send(embed=embed)

    try:
        synced = await bot.tree.sync()
        log.info(f"Synced {len(synced)} slash commands.")
    except Exception as e:
        log.error(e)

    log.info("Bot ready and operational!")

# -------------------
# Run Bot
# -------------------
bot.run(TOKEN)
