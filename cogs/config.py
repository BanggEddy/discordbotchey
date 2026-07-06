import discord
from discord import app_commands
from discord.ext import commands

from utils.helpers import load_config, save_config


class Config(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setlogs", description="📝 Définir le salon de logs")
    @app_commands.describe(salon="Salon pour les logs")
    @app_commands.checks.has_permissions(administrator=True)
    async def setlogs(self, interaction: discord.Interaction, salon: discord.TextChannel):
        self.bot.config["logs_channel_id"] = salon.id
        save_config(self.bot.config)
        await interaction.response.send_message(f"📝 Salon de logs défini sur {salon.mention}.")

    @app_commands.command(name="setwelcome", description="🎉 Définir le salon de bienvenue")
    @app_commands.describe(salon="Salon pour les messages de bienvenue")
    @app_commands.checks.has_permissions(administrator=True)
    async def setwelcome(self, interaction: discord.Interaction, salon: discord.TextChannel):
        self.bot.config["welcome_channel_id"] = salon.id
        save_config(self.bot.config)
        await interaction.response.send_message(f"🎉 Salon de bienvenue défini sur {salon.mention}.")

    @app_commands.command(name="setgoodbye", description="👋 Définir le salon d'au revoir")
    @app_commands.describe(salon="Salon pour les messages d'au revoir")
    @app_commands.checks.has_permissions(administrator=True)
    async def setgoodbye(self, interaction: discord.Interaction, salon: discord.TextChannel):
        self.bot.config["goodbye_channel_id"] = salon.id
        save_config(self.bot.config)
        await interaction.response.send_message(f"👋 Salon d'au revoir défini sur {salon.mention}.")

    @app_commands.command(name="help", description="📖 Afficher l'aide du bot")
    async def help_cmd(self, interaction: discord.Interaction):
        embed = discord.Embed(title="🤖 Aide du bot", color=discord.Color.blurple())
        embed.add_field(
            name="Modération",
            value=(
                "`/ping` — Latence\n"
                "`/ban` — Bannir\n"
                "`/kick` — Expulser\n"
                "`/mute` / `/unmute` — Timeout\n"
                "`/warn` / `/warns` — Avertissements\n"
                "`/clear` — Supprimer des messages"
            ),
            inline=False,
        )
        embed.add_field(
            name="Rôles & MP",
            value=(
                "`/role` — Ajouter/retirer un rôle\n"
                "`/roles` — Voir les rôles\n"
                "`/mp` — Message privé\n"
                "`/wakeup` — Réveiller par MP"
            ),
            inline=False,
        )
        embed.add_field(
            name="Utilisateurs",
            value=(
                "`/user follow` — Suivre un membre\n"
                "`/user unfollow` — Ne plus suivre\n"
                "`/user following` — Voir ta liste de suivi\n"
                "`/user find` — Localiser un membre"
            ),
            inline=False,
        )
        embed.add_field(
            name="Configuration",
            value=(
                "`/setlogs` — Salon de logs\n"
                "`/setwelcome` — Salon de bienvenue\n"
                "`/setgoodbye` — Salon d'au revoir"
            ),
            inline=False,
        )
        embed.add_field(
            name="Auto-modération",
            value="🤖 Anti-spam · 🚫 Anti-liens · 🤬 Anti-insultes (config dans config.json)",
            inline=False,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Config(bot))
