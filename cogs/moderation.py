import discord
from discord import app_commands
from discord.ext import commands

from utils.helpers import log_embed, send_log


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config

    @app_commands.command(name="ping", description="🏓 Vérifier la latence du bot")
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(f"🏓 Pong ! Latence : **{latency} ms**")

    @app_commands.command(name="ban", description="🔨 Bannir un membre")
    @app_commands.describe(membre="Membre à bannir", raison="Raison du ban")
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, membre: discord.Member, raison: str = "Aucune raison"):
        if membre.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("❌ Tu ne peux pas bannir ce membre.", ephemeral=True)
            return
        if not membre.bannable:
            await interaction.response.send_message("❌ Je ne peux pas bannir ce membre.", ephemeral=True)
            return

        await membre.ban(reason=f"{raison} | Par {interaction.user}")
        await interaction.response.send_message(f"🔨 **{membre}** a été banni.\n📝 Raison : {raison}")

        embed = log_embed(
            "🔨 Ban",
            discord.Color.red(),
            Membre=f"{membre} ({membre.id})",
            Modérateur=f"{interaction.user} ({interaction.user.id})",
            Raison=raison,
        )
        await send_log(self.bot, self.config, embed)

    @app_commands.command(name="kick", description="👢 Expulser un membre")
    @app_commands.describe(membre="Membre à expulser", raison="Raison du kick")
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, membre: discord.Member, raison: str = "Aucune raison"):
        if membre.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("❌ Tu ne peux pas expulser ce membre.", ephemeral=True)
            return
        if not membre.kickable:
            await interaction.response.send_message("❌ Je ne peux pas expulser ce membre.", ephemeral=True)
            return

        await membre.kick(reason=f"{raison} | Par {interaction.user}")
        await interaction.response.send_message(f"👢 **{membre}** a été expulsé.\n📝 Raison : {raison}")

        embed = log_embed(
            "👢 Kick",
            discord.Color.orange(),
            Membre=f"{membre} ({membre.id})",
            Modérateur=f"{interaction.user} ({interaction.user.id})",
            Raison=raison,
        )
        await send_log(self.bot, self.config, embed)

    @app_commands.command(name="mute", description="🔇 Rendre muet un membre (timeout)")
    @app_commands.describe(membre="Membre à mute", duree="Durée en minutes", raison="Raison")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def mute(
        self,
        interaction: discord.Interaction,
        membre: discord.Member,
        duree: app_commands.Range[int, 1, 40320] = None,
        raison: str = "Aucune raison",
    ):
        if membre.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("❌ Tu ne peux pas mute ce membre.", ephemeral=True)
            return

        minutes = duree or self.config.get("moderation", {}).get("mute_duration_minutes", 60)
        from datetime import timedelta

        await membre.timeout(timedelta(minutes=minutes), reason=f"{raison} | Par {interaction.user}")
        await interaction.response.send_message(
            f"🔇 **{membre}** est mute pour **{minutes} min**.\n📝 Raison : {raison}"
        )

        embed = log_embed(
            "🔇 Mute",
            discord.Color.dark_grey(),
            Membre=f"{membre} ({membre.id})",
            Modérateur=f"{interaction.user} ({interaction.user.id})",
            Durée=f"{minutes} min",
            Raison=raison,
        )
        await send_log(self.bot, self.config, embed)

    @app_commands.command(name="unmute", description="🔊 Retirer le mute d'un membre")
    @app_commands.describe(membre="Membre à unmute")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def unmute(self, interaction: discord.Interaction, membre: discord.Member):
        await membre.timeout(None, reason=f"Unmute par {interaction.user}")
        await interaction.response.send_message(f"🔊 **{membre}** n'est plus mute.")

    @app_commands.command(name="warn", description="⚠️ Avertir un membre")
    @app_commands.describe(membre="Membre à avertir", raison="Raison de l'avertissement")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def warn(self, interaction: discord.Interaction, membre: discord.Member, raison: str):
        from utils.helpers import guild_key, load_warns, save_warns, user_key

        warns = load_warns()
        gk = guild_key(interaction.guild.id)
        uk = user_key(membre.id)
        warns.setdefault(gk, {}).setdefault(uk, []).append(
            {"reason": raison, "mod": interaction.user.id, "date": discord.utils.utcnow().isoformat()}
        )
        save_warns(warns)
        count = len(warns[gk][uk])

        await interaction.response.send_message(
            f"⚠️ **{membre}** a reçu un avertissement.\n📝 Raison : {raison}\n📊 Total : **{count}** warn(s)"
        )

        embed = log_embed(
            "⚠️ Warn",
            discord.Color.gold(),
            Membre=f"{membre} ({membre.id})",
            Modérateur=f"{interaction.user} ({interaction.user.id})",
            Raison=raison,
            Total=str(count),
        )
        await send_log(self.bot, self.config, embed)

    @app_commands.command(name="warns", description="📋 Voir les avertissements d'un membre")
    @app_commands.describe(membre="Membre à consulter")
    @app_commands.checks.has_permissions(moderate_members=True)
    async def warns(self, interaction: discord.Interaction, membre: discord.Member):
        from utils.helpers import guild_key, load_warns, user_key

        warns = load_warns()
        user_warns = warns.get(guild_key(interaction.guild.id), {}).get(user_key(membre.id), [])

        if not user_warns:
            await interaction.response.send_message(f"✅ **{membre}** n'a aucun avertissement.", ephemeral=True)
            return

        lines = []
        for i, w in enumerate(user_warns, 1):
            lines.append(f"**#{i}** — {w['reason']}")

        embed = discord.Embed(title=f"⚠️ Warns de {membre.display_name}", color=discord.Color.gold())
        embed.description = "\n".join(lines)
        embed.set_footer(text=f"Total : {len(user_warns)} warn(s)")
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Moderation(bot))
