import json
from pathlib import Path

# Folder to store guild data
DATA_FOLDER = Path("guild_data")
DATA_FOLDER.mkdir(exist_ok=True)  # Create if not exists

def get_guild_file(guild_id: int) -> Path:
    """Return the path to a guild's JSON file."""
    return DATA_FOLDER / f"{guild_id}.json"

def get_guild_settings(guild_id: int) -> dict:
    """Load guild settings from JSON, or return default empty dict."""
    file_path = get_guild_file(guild_id)
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def set_guild_settings(guild_id: int, settings: dict):
    """Save guild settings to JSON with indentation for readability."""
    file_path = get_guild_file(guild_id)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4, ensure_ascii=False)

# -----------------------
# Config channel methods
# -----------------------
def get_config_channel_id(guild_id: int) -> int | None:
    """Return saved config channel ID if exists."""
    return get_guild_settings(guild_id).get("config_channel")

def set_config_channel_id(guild_id: int, channel_id: int):
    """Save config channel ID in guild settings."""
    settings = get_guild_settings(guild_id)
    settings["config_channel"] = channel_id
    set_guild_settings(guild_id, settings)

# -----------------------
# Disabled cogs methods
# -----------------------
def get_disabled_cogs(guild_id: int) -> list:
    """Return a list of cog names disabled for this guild."""
    settings = get_guild_settings(guild_id)
    return settings.get("disabled_cogs", [])

def set_disabled_cogs(guild_id: int, disabled: list):
    """Save the list of disabled cogs for this guild."""
    settings = get_guild_settings(guild_id)
    settings["disabled_cogs"] = disabled
    set_guild_settings(guild_id, settings)

def disable_cog_for_guild(guild_id: int, cog_name: str):
    """Disable a single cog for the guild."""
    disabled = get_disabled_cogs(guild_id)
    if cog_name not in disabled:
        disabled.append(cog_name)
        set_disabled_cogs(guild_id, disabled)

def enable_cog_for_guild(guild_id: int, cog_name: str):
    """Enable a single cog for the guild."""
    disabled = get_disabled_cogs(guild_id)
    if cog_name in disabled:
        disabled.remove(cog_name)
        set_disabled_cogs(guild_id, disabled)
