import discord
from discord import app_commands
from discord.ext import commands

from utils.helpers import log_embed, send_log


class Roles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config

    @app_commands.command(name="role", description="🎭 Ajouter ou retirer un rôle à un membre")
    @app_commands.describe(action="Action à effectuer", membre="Membre ciblé", role="Rôle concerné")
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
            await interaction.response.send_message("❌ Ce rôle est au-dessus du mien.", ephemeral=True)
            return
        if role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("❌ Tu ne peux pas gérer ce rôle.", ephemeral=True)
            return

        if action == "add":
            if role in membre.roles:
                await interaction.response.send_message(f"ℹ️ **{membre}** a déjà le rôle {role.mention}.", ephemeral=True)
                return
            await membre.add_roles(role, reason=f"Ajouté par {interaction.user}")
            await interaction.response.send_message(f"✅ Rôle {role.mention} ajouté à **{membre}**.")
            action_label = "Ajout"
        else:
            if role not in membre.roles:
                await interaction.response.send_message(f"ℹ️ **{membre}** n'a pas le rôle {role.mention}.", ephemeral=True)
                return
            await membre.remove_roles(role, reason=f"Retiré par {interaction.user}")
            await interaction.response.send_message(f"✅ Rôle {role.mention} retiré de **{membre}**.")
            action_label = "Retrait"

        embed = log_embed(
            f"🎭 {action_label} de rôle",
            discord.Color.blue(),
            Membre=f"{membre} ({membre.id})",
            Rôle=f"{role.name} ({role.id})",
            Modérateur=f"{interaction.user} ({interaction.user.id})",
        )
        await send_log(self.bot, self.config, embed)

    @app_commands.command(name="roles", description="🎭 Lister les rôles d'un membre")
    @app_commands.describe(membre="Membre à consulter")
    async def roles(self, interaction: discord.Interaction, membre: discord.Member = None):
        membre = membre or interaction.user
        roles = [r.mention for r in reversed(membre.roles) if r.name != "@everyone"]
        if not roles:
            await interaction.response.send_message(f"**{membre}** n'a aucun rôle.", ephemeral=True)
            return
        embed = discord.Embed(title=f"🎭 Rôles de {membre.display_name}", color=membre.color)
        embed.description = " ".join(roles)
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Roles(bot))
