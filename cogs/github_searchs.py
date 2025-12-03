import discord
from discord.ext import commands
from discord import app_commands
import requests
from utils.embed_utils import create_modern_embed
import re
import os

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")  # Loaded from .env

class GitHub(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # -----------------------
    # Helper Functions
    # -----------------------
    def github_request(self, url: str):
        """Perform a GET request to GitHub API with token if available."""
        headers = {"Accept": "application/vnd.github+json"}
        if GITHUB_TOKEN:
            headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
        return requests.get(url, headers=headers, timeout=5)

    def extract_repo(self, url: str):
        """Extract owner/repo from a GitHub URL."""
        match = re.search(r"github\.com/([^/]+)/([^/]+)", url)
        return match.groups() if match else None

    # -----------------------
    # Repository Info
    # -----------------------
    @app_commands.command(name="repo", description="Get information about a GitHub repository.")
    async def repo(self, interaction: discord.Interaction, github_link: str):
        await interaction.response.defer()
        extracted = self.extract_repo(github_link)
        if not extracted:
            return await interaction.followup.send("❌ Invalid GitHub URL. Example: https://github.com/owner/repo")
        owner, repo_name = extracted
        api_url = f"https://api.github.com/repos/{owner}/{repo_name}"

        try:
            resp = self.github_request(api_url)
            if resp.status_code == 404:
                embed = create_modern_embed(
                    title="❌ Repository Not Found",
                    description=f"The repository **{owner}/{repo_name}** does not exist or is private.",
                    color=0xFF5555
                )
                return await interaction.followup.send(embed=embed)
            repo = resp.json()

            # Repo details
            stars = repo.get("stargazers_count", 0)
            forks = repo.get("forks_count", 0)
            open_issues = repo.get("open_issues_count", 0)
            lang = repo.get("language") or "Unknown"
            visibility = "🔓 Public" if not repo.get("private") else "🔒 Private"
            archived = "📦 Archived" if repo.get("archived") else "🟢 Active"
            html_url = repo.get("html_url")
            desc = repo.get("description") or "No description."
            updated = repo.get("updated_at", "").replace("T", " ").replace("Z", "")
            topics = ", ".join(repo.get("topics", [])) or "None"

            # Last commit
            last_commit = "Unknown"
            commits_url = repo.get("commits_url", "").replace("{/sha}", "")
            try:
                commits_resp = self.github_request(commits_url)
                if commits_resp.status_code == 200 and commits_resp.json():
                    last_commit = commits_resp.json()[0]["commit"]["message"]
            except:
                pass

            # Embed
            embed = create_modern_embed(
                title=f"📘 GitHub Repo Info",
                description=f"**[{owner}/{repo_name}]({html_url})**\n{visibility} • {archived}",
                color=0x2b3137
            )
            embed.add_field(name="⭐ Stars", value=str(stars), inline=True)
            embed.add_field(name="🍴 Forks", value=str(forks), inline=True)
            embed.add_field(name="🐛 Open Issues", value=str(open_issues), inline=True)
            embed.add_field(name="📌 Language", value=lang, inline=True)
            embed.add_field(name="📝 Description", value=desc, inline=False)
            embed.add_field(name="🗂 Topics", value=topics, inline=False)
            embed.add_field(name="💻 Last Commit", value=last_commit, inline=False)
            embed.add_field(name="⏱ Last Updated", value=updated, inline=True)

            # Buttons
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="Open Repo", url=html_url))
            view.add_item(discord.ui.Button(label="Issues", url=f"{html_url}/issues"))
            view.add_item(discord.ui.Button(label="PRs", url=f"{html_url}/pulls"))
            view.add_item(discord.ui.Button(label="Releases", url=f"{html_url}/releases"))

            await interaction.followup.send(embed=embed, view=view)

        except requests.exceptions.RequestException:
            await interaction.followup.send("⚠️ Could not reach GitHub API.")

    # -----------------------
    # Search Repositories
    # -----------------------
    @app_commands.command(name="search_repo", description="Search GitHub repositories by keyword.")
    async def search_repo(self, interaction: discord.Interaction, query: str):
        await interaction.response.defer()
        url = f"https://api.github.com/search/repositories?q={query}&sort=stars&order=desc&per_page=5"
        try:
            resp = self.github_request(url)
            if resp.status_code != 200:
                return await interaction.followup.send("⚠️ Error searching repositories.")
            data = resp.json().get("items", [])
            if not data:
                return await interaction.followup.send("❌ No repositories found.")

            desc = ""
            for repo in data:
                desc += f"**[{repo['full_name']}]({repo['html_url']})** ⭐ {repo['stargazers_count']}\n{repo.get('description') or 'No description'}\n\n"

            embed = create_modern_embed(
                title=f"🔍 GitHub Search: {query}",
                description=desc,
                color=0x2b3137
            )
            await interaction.followup.send(embed=embed)
        except requests.exceptions.RequestException:
            await interaction.followup.send("⚠️ Could not reach GitHub API.")

    # -----------------------
    # User Info
    # -----------------------
    @app_commands.command(name="github_user", description="Get GitHub user info.")
    async def github_user(self, interaction: discord.Interaction, username: str):
        await interaction.response.defer()
        url = f"https://api.github.com/users/{username}"
        try:
            resp = self.github_request(url)
            if resp.status_code == 404:
                return await interaction.followup.send(f"❌ User `{username}` not found.")
            user = resp.json()
            login = user["login"]
            name = user.get("name") or "N/A"
            bio = user.get("bio") or "No bio"
            avatar = user.get("avatar_url")
            followers = user.get("followers", 0)
            following = user.get("following", 0)
            public_repos = user.get("public_repos", 0)
            profile_url = user.get("html_url")

            # Top 5 repos
            repos_resp = self.github_request(f"https://api.github.com/users/{username}/repos?sort=stars&per_page=5")
            repos_text = ""
            if repos_resp.status_code == 200:
                for r in repos_resp.json():
                    repos_text += f"**[{r['name']}]({r['html_url']})** ⭐ {r['stargazers_count']}\n"

            embed = create_modern_embed(
                title=f"👤 GitHub User: {login}",
                description=bio,
                color=0x2b3137
            )
            embed.set_thumbnail(url=avatar)
            embed.add_field(name="Name", value=name, inline=True)
            embed.add_field(name="Followers", value=str(followers), inline=True)
            embed.add_field(name="Following", value=str(following), inline=True)
            embed.add_field(name="Public Repos", value=str(public_repos), inline=True)
            if repos_text:
                embed.add_field(name="Top Repos", value=repos_text, inline=False)

            # Buttons
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="Profile", url=profile_url))
            view.add_item(discord.ui.Button(label="Repos", url=f"{profile_url}?tab=repositories"))
            view.add_item(discord.ui.Button(label="Followers", url=f"{profile_url}?tab=followers"))
            view.add_item(discord.ui.Button(label="Following", url=f"{profile_url}?tab=following"))

            await interaction.followup.send(embed=embed, view=view)

        except requests.exceptions.RequestException:
            await interaction.followup.send("⚠️ Could not reach GitHub API.")

    # -----------------------
    # Recent Commits
    # -----------------------
    @app_commands.command(name="user_commits", description="Show recent commits of a user or a specific repo.")
    async def user_commits(self, interaction: discord.Interaction, username: str, repo: str = None):
        await interaction.response.defer()
        try:
            if repo:
                # Specific repo
                commits_url = f"https://api.github.com/repos/{username}/{repo}/commits?per_page=5"
            else:
                # All public repos - take top repo by stars
                repos_resp = self.github_request(f"https://api.github.com/users/{username}/repos?sort=stars&per_page=1")
                if repos_resp.status_code != 200 or not repos_resp.json():
                    return await interaction.followup.send("❌ Could not fetch repos.")
                repo_name = repos_resp.json()[0]["name"]
                commits_url = f"https://api.github.com/repos/{username}/{repo_name}/commits?per_page=5"

            commits_resp = self.github_request(commits_url)
            if commits_resp.status_code != 200:
                return await interaction.followup.send("❌ Could not fetch commits.")

            commits = commits_resp.json()
            desc = ""
            for c in commits:
                msg = c["commit"]["message"]
                url = c["html_url"]
                date = c["commit"]["committer"]["date"].replace("T", " ").replace("Z", "")
                desc += f"[{msg}]({url}) ⏱ {date}\n\n"

            embed = create_modern_embed(
                title=f"📝 Recent Commits - {username}",
                description=desc,
                color=0x2b3137
            )
            await interaction.followup.send(embed=embed)

        except requests.exceptions.RequestException:
            await interaction.followup.send("⚠️ Could not reach GitHub API.")


async def setup(bot):
    await bot.add_cog(GitHub(bot))
