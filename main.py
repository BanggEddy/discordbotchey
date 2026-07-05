import asyncio
import os

import discord
from discord.ext import commands

from utils.helpers import load_config


intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True


class Bot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.config = load_config()

    async def setup_hook(self):
        cogs = [
            "cogs.moderation",
            "cogs.automod",
            "cogs.welcome",
            "cogs.roles",
            "cogs.dm",
            "cogs.users",
            "cogs.config",
        ]
        for cog in cogs:
            await self.load_extension(cog)

        guild_id = self.config.get("guild_id")
        if guild_id:
            guild = discord.Object(id=guild_id)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()

    async def on_ready(self):
        print(f"✅ Connecté en tant que {self.user}")
        print(f"📡 Présent sur {len(self.guilds)} serveur(s)")


async def main():
    bot = Bot()
    await bot.start(bot.config["token"])


if __name__ == "__main__":
    asyncio.run(main())
