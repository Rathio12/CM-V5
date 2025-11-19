from discord.ext import commands
import aiohttp, random

class FunCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sent_messages = set()  # Keep track to prevent duplicate sending

    @commands.command(name="meme")
    async def meme(self, ctx):
        """Fetch a single meme from r/memes and send it once."""
        # Prevent double sending from overlapping commands
        if ctx.message.id in self.sent_messages:
            return
        self.sent_messages.add(ctx.message.id)

        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://www.reddit.com/r/memes/hot.json?limit=50",
                headers={"User-agent": "CM-V5.3"}
            ) as r:
                if r.status != 200:
                    await ctx.send("❌ Failed to fetch memes from Reddit.")
                    return
                
                data = await r.json()
                posts = [
                    p["data"] for p in data["data"]["children"]
                    if not p["data"]["stickied"] and p["data"].get("url", "").endswith((".jpg", ".png", ".gif", ".jpeg"))
                ]

                if not posts:
                    await ctx.send("❌ No valid memes found.")
                    return
                
                post = random.choice(posts)
                await ctx.send(post["url"])

        # Remove the message id after sending to free memory
        self.sent_messages.discard(ctx.message.id)

    @commands.command(name="sm")
    async def say_message(self, ctx, *, text: str):
        """Repeat a message."""
        await ctx.send(text)

async def setup(bot):
    await bot.add_cog(FunCog(bot))
