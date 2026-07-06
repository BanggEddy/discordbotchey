import discord
from discord import app_commands
from discord.ext import commands

from utils.helpers import log_embed, send_log


class DM(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config

    @app_commands.command(name="mp", description="Envoyer un message prive a un membre")
    @app_commands.describe(membre="Destinataire", message="Contenu du MP")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def mp(self, interaction: discord.Interaction, membre: discord.Member, message: str):
        try:
            embed = discord.Embed(
                title="Message du staff",
                description=message,
                color=discord.Color.blurple(),
            )
            embed.set_footer(text=f"Serveur : {interaction.guild.name}")
            await membre.send(embed=embed)
        except discord.HTTPException:
            await interaction.response.send_message(
                f"Impossible d'envoyer un MP a **{membre}** (MPs fermes).",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(f"MP envoye a **{membre}**.", ephemeral=True)

        embed = log_embed(
            "MP envoye",
            discord.Color.blurple(),
            Destinataire=f"{membre} ({membre.id})",
            Expediteur=f"{interaction.user} ({interaction.user.id})",
            Message=message[:1000],
        )
        await send_log(self.bot, self.config, embed)

    @app_commands.command(name="wakeup", description="Reveiller un membre par MP")
    @app_commands.describe(membre="Membre a reveiller", message="Message de reveil (optionnel)")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def wakeup(
        self,
        interaction: discord.Interaction,
        membre: discord.Member,
        message: str = None,
    ):
        wake_msg = message or "**REVEIL !** On t'attend sur le serveur !"
        full_message = (
            f"# WAKE UP !\n\n"
            f"{membre.mention}\n\n"
            f"{wake_msg}\n\n"
            f"- Envoye depuis **{interaction.guild.name}**"
        )

        try:
            await membre.send(full_message)
        except discord.HTTPException:
            await interaction.response.send_message(
                f"Impossible de reveiller **{membre}** (MPs fermes).",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(f"**{membre}** a ete reveille par MP !")

        embed = log_embed(
            "Wake up",
            discord.Color.yellow(),
            Membre=f"{membre} ({membre.id})",
            Par=f"{interaction.user} ({interaction.user.id})",
            Message=wake_msg[:500],
        )
        await send_log(self.bot, self.config, embed)


async def setup(bot):
    await bot.add_cog(DM(bot))
