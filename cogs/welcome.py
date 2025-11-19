import discord
from discord.ext import commands
from utils.embed_utils import create_modern_embed

# Replace these with your actual support server link and GitHub repo
SUPPORT_SERVER_LINK = "https://discord.gg/x2n5RF6fKd"
GITHUB_REPO_LINK = "https://github.com/Rathio12/CM-V5-/blob/main/README.MD"  # <-- replace with your repo

class WelcomeCog(commands.Cog):
    """Sends a welcome DM to the server owner when the bot is added."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        owner = guild.owner
        if not owner:
            return  # Owner info missing

        try:
            description = (
                "**// THANKS FOR ADDING ME TO YOUR SERVER!! //**\n"
                "*Still getting developed, so don't be frustrated if something doesn't work on the first try.*\n\n"
                "**1️⃣ You can use `/setup` to configure logging channels.**\n"
                "**2️⃣ `?meme` for a quick Reddit meme.**\n"
                "**3️⃣ You can do `/cog_list` and `/cog_enable` or `/cog_disable` to manage cogs.**\n\n"
                f"💬 Support server: [Click here]({SUPPORT_SERVER_LINK})\n"
                f"📄 GitHub Repo / README: [Click here]({GITHUB_REPO_LINK})"
            )

            embed = create_modern_embed(
                title="🤖 Welcome!",
                description=description,
                color=discord.Color.green(),
                emoji_prefix="👋"
            )

            await owner.send(embed=embed)
        except discord.Forbidden:
            print(f"[WELCOME] Could not DM owner of {guild.name} ({owner})")

async def setup(bot: commands.Bot):
    await bot.add_cog(WelcomeCog(bot))
