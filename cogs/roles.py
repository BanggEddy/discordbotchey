import discord
from discord import app_commands
from discord.ext import commands

from utils.helpers import log_command_use, log_embed, send_log


class Roles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config

    @app_commands.command(name="role", description="Ajouter ou retirer un role a un membre")
    @app_commands.describe(action="Action a effectuer", membre="Membre cible", role="Role concerne")
    @app_commands.choices(
        action=[
            app_commands.Choice(name="Ajouter", value="add"),
            app_commands.Choice(name="Retirer", value="remove"),
        ]
    )
    @app_commands.checks.has_permissions(manage_roles=True)
    async def role(
        self,
        interaction: discord.Interaction,
        action: str,
        membre: discord.Member,
        role: discord.Role,
    ):
        if role >= interaction.guild.me.top_role:
            await interaction.response.send_message("Ce role est au-dessus du mien.", ephemeral=True)
            return
        if role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("Tu ne peux pas gerer ce role.", ephemeral=True)
            return

        if action == "add":
            if role in membre.roles:
                await interaction.response.send_message(
                    f"**{membre}** a deja le role {role.mention}.", ephemeral=True
                )
                return
            await membre.add_roles(role, reason=f"Ajoute par {interaction.user}")
            await interaction.response.send_message(f"Role {role.mention} ajoute a **{membre}**.")
            action_label = "Ajout"
        else:
            if role not in membre.roles:
                await interaction.response.send_message(
                    f"**{membre}** n'a pas le role {role.mention}.", ephemeral=True
                )
                return
            await membre.remove_roles(role, reason=f"Retire par {interaction.user}")
            await interaction.response.send_message(f"Role {role.mention} retire de **{membre}**.")
            action_label = "Retrait"

        embed = log_embed(
            f"{action_label} de role",
            discord.Color.blue(),
            Membre=f"{membre} ({membre.id})",
            Role=f"{role.name} ({role.id})",
            Moderateur=f"{interaction.user} ({interaction.user.id})",
        )
        await send_log(self.bot, self.config, embed)

    @app_commands.command(name="roles", description="Lister les roles d'un membre")
    @app_commands.describe(membre="Membre a consulter")
    async def roles(self, interaction: discord.Interaction, membre: discord.Member = None):
        membre = membre or interaction.user
        roles = [r.mention for r in reversed(membre.roles) if r.name != "@everyone"]
        if not roles:
            await interaction.response.send_message(f"**{membre}** n'a aucun role.", ephemeral=True)
            await log_command_use(
                self.bot,
                self.config,
                interaction,
                "roles",
                Membre=f"{membre} ({membre.id})",
                Total="0",
            )
            return
        embed = discord.Embed(title=f"Roles de {membre.display_name}", color=membre.color)
        embed.description = " ".join(roles)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await log_command_use(
            self.bot,
            self.config,
            interaction,
            "roles",
            Membre=f"{membre} ({membre.id})",
            Total=str(len(roles)),
        )


async def setup(bot):
    await bot.add_cog(Roles(bot))
