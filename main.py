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
        self._commands_synced = False

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

    async def sync_commands(self):
        guild_id = self.config.get("guild_id")
        synced = []

        if guild_id:
            guild = discord.Object(id=guild_id)
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
        else:
            for guild in self.guilds:
                self.tree.copy_global_to(guild=guild)
                synced.extend(await self.tree.sync(guild=guild))
            if not synced:
                synced = await self.tree.sync()

        names = sorted({cmd.name for cmd in synced})
        print(f"{len(names)} commande(s) slash synchronisee(s) : {', '.join(f'/{n}' for n in names)}")
        return synced

    async def on_ready(self):
        print(f"Connecte en tant que {self.user}")
        print(f"Present sur {len(self.guilds)} serveur(s)")

        if not self._commands_synced:
            self._commands_synced = True
            await self.sync_commands()


async def main():
    bot = Bot()
    await bot.start(bot.config["token"])


if __name__ == "__main__":
    asyncio.run(main())
