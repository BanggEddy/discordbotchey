import json
import os
from datetime import datetime, timezone

import discord
from dotenv import load_dotenv

load_dotenv()


def load_config():
    config_path = "config.json"
    if not os.path.exists(config_path):
        config_path = "config.example.json"
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise ValueError(
            "DISCORD_TOKEN manquant. Copie .env.example vers .env et ajoute ton token."
        )
    config["token"] = token
    return config


def save_config(config):
    with open("config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)


def ensure_data_dir():
    os.makedirs("data", exist_ok=True)


def load_warns():
    ensure_data_dir()
    path = "data/warns.json"
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_warns(warns):
    ensure_data_dir()
    with open("data/warns.json", "w", encoding="utf-8") as f:
        json.dump(warns, f, indent=4, ensure_ascii=False)


def load_follows():
    ensure_data_dir()
    path = "data/follows.json"
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_follows(follows):
    ensure_data_dir()
    with open("data/follows.json", "w", encoding="utf-8") as f:
        json.dump(follows, f, indent=4, ensure_ascii=False)


def get_followers(follows, guild_id, target_id):
    gk = guild_key(guild_id)
    tk = user_key(target_id)
    result = []
    for follower_id, targets in follows.get(gk, {}).items():
        if tk in targets:
            result.append(int(follower_id))
    return result


def guild_key(guild_id):
    return str(guild_id)


def user_key(user_id):
    return str(user_id)


async def send_log(bot, config, embed: discord.Embed):
    channel_id = config.get("logs_channel_id")
    if not channel_id:
        return
    channel = bot.get_channel(channel_id)
    if channel is None:
        try:
            channel = await bot.fetch_channel(channel_id)
        except discord.HTTPException:
            return
    if channel:
        await channel.send(embed=embed)


def log_embed(title: str, color: discord.Color, **fields):
    embed = discord.Embed(
        title=title,
        color=color,
        timestamp=datetime.now(timezone.utc),
    )
    for name, value in fields.items():
        if value is not None:
            embed.add_field(name=name, value=value, inline=True)
    return embed


def has_bypass(member: discord.Member, config) -> bool:
    bypass_ids = config.get("automod", {}).get("bypass_role_ids", [])
    return any(role.id in bypass_ids for role in member.roles)


def is_moderator(member: discord.Member) -> bool:
    perms = member.guild_permissions
    return perms.administrator or perms.ban_members or perms.kick_members or perms.moderate_members
