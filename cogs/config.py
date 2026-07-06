import discord
from discord import app_commands
from discord.ext import commands

from utils.helpers import load_config, log_command_use, log_embed, save_config, send_log


class Config(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setlogs", description="Definir le salon de logs")
    @app_commands.describe(salon="Salon pour les logs")
    @app_commands.checks.has_permissions(administrator=True)
    async def setlogs(self, interaction: discord.Interaction, salon: discord.TextChannel):
        self.bot.config["logs_channel_id"] = salon.id
        save_config(self.bot.config)

        test_embed = log_embed(
            "Logs configures",
            discord.Color.green(),
            Moderateur=f"{interaction.user} ({interaction.user.id})",
            Salon=salon.mention,
        )
        ok = await send_log(self.bot, self.bot.config, test_embed)

        if ok:
            await interaction.response.send_message(
                f"Salon de logs defini sur {salon.mention}. Un message test a ete envoye.",
            )
        else:
            await interaction.response.send_message(
                f"Salon enregistre ({salon.mention}), mais le bot n'a pas pu y ecrire.\n"
                f"Verifie qu'il a les permissions **Voir le salon**, **Envoyer des messages** "
                f"et **Integrer des liens** dans ce salon.",
                ephemeral=True,
            )

    @app_commands.command(name="setwelcome", description="Definir le salon de bienvenue")
    @app_commands.describe(salon="Salon pour les messages de bienvenue")
    @app_commands.checks.has_permissions(administrator=True)
    async def setwelcome(self, interaction: discord.Interaction, salon: discord.TextChannel):
        self.bot.config["welcome_channel_id"] = salon.id
        save_config(self.bot.config)
        await interaction.response.send_message(f"Salon de bienvenue defini sur {salon.mention}.")
        await log_command_use(self.bot, self.bot.config, interaction, "setwelcome", Salon=salon.mention)

    @app_commands.command(name="setgoodbye", description="Definir le salon d'au revoir")
    @app_commands.describe(salon="Salon pour les messages d'au revoir")
    @app_commands.checks.has_permissions(administrator=True)
    async def setgoodbye(self, interaction: discord.Interaction, salon: discord.TextChannel):
        self.bot.config["goodbye_channel_id"] = salon.id
        save_config(self.bot.config)
        await interaction.response.send_message(f"Salon d'au revoir defini sur {salon.mention}.")
        await log_command_use(self.bot, self.bot.config, interaction, "setgoodbye", Salon=salon.mention)

    @app_commands.command(name="help", description="Afficher l'aide du bot")
    async def help_cmd(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Aide du bot", color=discord.Color.blurple())
        embed.add_field(
            name="Moderation",
            value=(
                "`/ping` - Latence\n"
                "`/ban` - Bannir\n"
                "`/kick` - Expulser\n"
                "`/mute` / `/unmute` - Timeout\n"
                "`/warn` / `/warns` - Avertissements\n"
                "`/clear` - Supprimer des messages"
            ),
            inline=False,
        )
        embed.add_field(
            name="Roles & MP",
            value=(
                "`/role` - Ajouter/retirer un role\n"
                "`/roles` - Voir les roles\n"
                "`/mp` - Message prive\n"
                "`/wakeup` - Reveiller par MP"
            ),
            inline=False,
        )
        embed.add_field(
            name="Utilisateurs",
            value=(
                "`/followuser` - Suivre un membre\n"
                "`/find` - Localiser un membre\n"
                "`/user unfollow` - Ne plus suivre\n"
                "`/user following` - Voir ta liste de suivi"
            ),
            inline=False,
        )
        embed.add_field(
            name="Configuration",
            value=(
                "`/setlogs` - Salon de logs\n"
                "`/setwelcome` - Salon de bienvenue\n"
                "`/setgoodbye` - Salon d'au revoir"
            ),
            inline=False,
        )
        embed.add_field(
            name="Auto-moderation",
            value="Anti-spam, anti-liens, anti-insultes (config dans config.json)",
            inline=False,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await log_command_use(self.bot, self.bot.config, interaction, "help")


async def setup(bot):
    await bot.add_cog(Config(bot))
