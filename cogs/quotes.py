import discord
from discord.ext import commands, tasks
from discord import app_commands
from utils.embed_utils import create_modern_embed
import aiohttp
import random

# Subreddits for quotes/facts
REDDIT_SUBREDDITS = ["quotes", "facts"]

class QuotesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.post_channel_id = None
        self.quote_loop.start()

    # -----------------------------
    # Scheduled quote/fact posting
    # -----------------------------
    @tasks.loop(hours=2)
    async def quote_loop(self):
        await self.bot.wait_until_ready()
        if not self.post_channel_id:
            return
        channel = self.bot.get_channel(self.post_channel_id)
        if not channel:
            return

        quote = await self.get_random_quote()
        embed = create_modern_embed(
            title="💡 Quote / Fact",
            description=quote,
            color=discord.Color.blue()
        )
        await channel.send(embed=embed)

    # -----------------------------
    # Slash command for random quote/fact
    # -----------------------------
    @app_commands.command(name="quote", description="Get a random quote or fact from the internet")
    async def quote(self, interaction: discord.Interaction):
        quote = await self.get_random_quote()
        embed = create_modern_embed(
            title="💡 Quote / Fact",
            description=quote,
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed)

    # -----------------------------
    # Admin command to set channel
    # -----------------------------
    @app_commands.command(name="set_quote_channel", description="Set channel for scheduled quotes/facts")
    async def set_quote_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        self.post_channel_id = channel.id
        await interaction.response.send_message(f"✅ Quote/fact channel set to {channel.mention}", ephemeral=True)

    # -----------------------------
    # Helper: get random quote/fact
    # -----------------------------
    async def get_random_quote(self) -> str:
        # Shuffle sources for variety
        sources = [self.fetch_quote_garden, self.fetch_zenquotes, self.fetch_reddit]
        random.shuffle(sources)

        for source in sources:
            try:
                quote = await source()
                if quote:
                    return quote
            except Exception:
                continue

        return "⚠️ Could not fetch quote/fact from online sources."

    # -----------------------------
    # Quote Garden API
    # -----------------------------
    async def fetch_quote_garden(self) -> str:
        url = "https://quote-garden.herokuapp.com/api/v3/quotes/random"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    q = data.get("data")[0]
                    return f"{q.get('quoteText')} — {q.get('quoteAuthor', 'Unknown')}"
        return None

    # -----------------------------
    # ZenQuotes API
    # -----------------------------
    async def fetch_zenquotes(self) -> str:
        url = "https://zenquotes.io/api/random"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if isinstance(data, list) and len(data) > 0:
                        return f"{data[0].get('q')} — {data[0].get('a')}"
        return None

    # -----------------------------
    # Reddit API
    # -----------------------------
    async def fetch_reddit(self) -> str:
        subreddit = random.choice(REDDIT_SUBREDDITS)
        url = f"https://www.reddit.com/r/{subreddit}/top.json?limit=50&t=all"
        headers = {"User-Agent": "DiscordBot"}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    posts = data.get("data", {}).get("children", [])
                    text_posts = [p["data"]["title"] for p in posts if p["data"]["selftext"] or p["data"]["title"]]
                    if text_posts:
                        return random.choice(text_posts)
        return None

# -----------------------------
# Setup function
# -----------------------------
async def setup(bot):
    await bot.add_cog(QuotesCog(bot))
