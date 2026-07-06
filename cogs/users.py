from datetime import datetime, timedelta

import discord
from discord import app_commands
from discord.ext import commands

from utils.helpers import get_followers, guild_key, load_follows, log_command_use, save_follows, user_key

STATUS_LABELS = {
    discord.Status.online: "En ligne",
    discord.Status.idle: "Inactif",
    discord.Status.dnd: "Ne pas déranger",
    discord.Status.offline: "Hors ligne",
    discord.Status.invisible: "Invisible",
}


class Users(commands.Cog):
    user = app_commands.Group(name="user", description="Suivi et recherche de membres")

    def __init__(self, bot):
        self.bot = bot
        self.last_seen = {}
        self._notify_cooldown = {}

    def _follow_enabled(self) -> bool:
        return self.bot.config.get("followuser_enabled", True)

    def _record_seen(self, member: discord.Member, channel: discord.abc.GuildChannel):
        self.last_seen[(member.guild.id, member.id)] = channel

    def _can_notify(self, follower_id: int, target_id: int, cooldown_seconds: int = 300) -> bool:
        key = (follower_id, target_id)
        now = datetime.utcnow()
        last = self._notify_cooldown.get(key)
        if last and now - last < timedelta(seconds=cooldown_seconds):
            return False
        self._notify_cooldown[key] = now
        return True

    def _build_find_embed(self, membre: discord.Member) -> discord.Embed:
        status = STATUS_LABELS.get(membre.status, "Inconnu")

        voice = None
        if membre.voice and membre.voice.channel:
            voice = membre.voice.channel.mention

        activity = None
        if membre.activity:
            if isinstance(membre.activity, discord.Spotify):
                activity = f"Écoute **{membre.activity.title}** - {membre.activity.artist}"
            elif isinstance(membre.activity, discord.Game):
                activity = f"Joue à **{membre.activity.name}**"
            elif isinstance(membre.activity, discord.Streaming):
                activity = f"Stream **{membre.activity.name}**"
            else:
                activity = membre.activity.name

        last_channel = self.last_seen.get((membre.guild.id, membre.id))
        last_channel_text = last_channel.mention if last_channel else "Inconnu"

        roles = [r.mention for r in reversed(membre.roles) if r.name != "@everyone"]
        roles_text = " ".join(roles[:10]) if roles else "Aucun"

        embed = discord.Embed(
            title=f"Localisation - {membre.display_name}",
            color=membre.color if membre.color.value else discord.Color.blurple(),
        )
        embed.set_thumbnail(url=membre.display_avatar.url)
        embed.add_field(name="Statut", value=status, inline=True)
        embed.add_field(name="Salon vocal", value=voice or "Pas en vocal", inline=True)
        embed.add_field(name="Activité", value=activity or "Aucune", inline=True)
        embed.add_field(name="Dernier salon textuel", value=last_channel_text, inline=True)
        embed.add_field(name="Pseudo", value=membre.name, inline=True)
        embed.add_field(name="ID", value=str(membre.id), inline=True)
        embed.add_field(name="Rôles", value=roles_text, inline=False)
        embed.add_field(
            name="A rejoint le serveur",
            value=discord.utils.format_dt(membre.joined_at, "R") if membre.joined_at else "Inconnu",
            inline=True,
        )
        embed.add_field(
            name="Compte créé",
            value=discord.utils.format_dt(membre.created_at, "R"),
            inline=True,
        )
        return embed

    async def _do_follow(self, interaction: discord.Interaction, membre: discord.Member, command: str):
        if not self._follow_enabled():
            await interaction.response.send_message(
                "Le suivi de membres est désactivé sur ce bot.", ephemeral=True
            )
            await log_command_use(
                self.bot,
                self.bot.config,
                interaction,
                command,
                Membre=f"{membre} ({membre.id})",
                Resultat="Desactive",
            )
            return
        if membre.id == interaction.user.id:
            await interaction.response.send_message("Tu ne peux pas te suivre toi-même.", ephemeral=True)
            await log_command_use(
                self.bot,
                self.bot.config,
                interaction,
                command,
                Membre=f"{membre} ({membre.id})",
                Resultat="Refuse (soi-meme)",
            )
            return
        if membre.bot:
            await interaction.response.send_message("Tu ne peux pas suivre un bot.", ephemeral=True)
            await log_command_use(
                self.bot,
                self.bot.config,
                interaction,
                command,
                Membre=f"{membre} ({membre.id})",
                Resultat="Refuse (bot)",
            )
            return

        follows = load_follows()
        gk = guild_key(interaction.guild.id)
        uk = user_key(interaction.user.id)
        tk = user_key(membre.id)
        follows.setdefault(gk, {}).setdefault(uk, [])

        if tk in follows[gk][uk]:
            await interaction.response.send_message(f"Tu suis déjà **{membre.display_name}**.", ephemeral=True)
            await log_command_use(
                self.bot,
                self.bot.config,
                interaction,
                command,
                Membre=f"{membre} ({membre.id})",
                Resultat="Deja suivi",
            )
            return

        follows[gk][uk].append(tk)
        save_follows(follows)
        await interaction.response.send_message(
            f"Tu suis maintenant **{membre.display_name}**.\n"
            f"Tu seras notifié par MP quand il se connecte, rejoint un vocal ou envoie un message.",
            ephemeral=True,
        )
        await log_command_use(
            self.bot,
            self.bot.config,
            interaction,
            command,
            Membre=f"{membre} ({membre.id})",
            Resultat="Suivi",
        )

    async def _notify_followers(
        self, guild: discord.Guild, target: discord.Member, message: str, cooldown: bool = False
    ):
        if not self._follow_enabled():
            return
        follows = load_follows()
        for follower_id in get_followers(follows, guild.id, target.id):
            if follower_id == target.id:
                continue
            if cooldown and not self._can_notify(follower_id, target.id):
                continue
            follower = guild.get_member(follower_id)
            if not follower:
                continue
            try:
                embed = discord.Embed(
                    title="Suivi utilisateur",
                    description=message,
                    color=discord.Color.teal(),
                )
                embed.set_thumbnail(url=target.display_avatar.url)
                embed.set_footer(text=f"Serveur : {guild.name}")
                await follower.send(embed=embed)
            except discord.HTTPException:
                pass

    @app_commands.command(name="find", description="Trouver où est un membre")
    @app_commands.describe(membre="Membre à localiser")
    async def find(self, interaction: discord.Interaction, membre: discord.Member):
        embed = self._build_find_embed(membre)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await log_command_use(
            self.bot, self.bot.config, interaction, "find", Membre=f"{membre} ({membre.id})"
        )

    @app_commands.command(name="followuser", description="Suivre un membre (notifications par MP)")
    @app_commands.describe(membre="Membre à suivre")
    async def followuser(self, interaction: discord.Interaction, membre: discord.Member):
        await self._do_follow(interaction, membre, "followuser")

    @user.command(name="follow", description="Suivre un membre (notifications par MP)")
    @app_commands.describe(membre="Membre à suivre")
    async def follow(self, interaction: discord.Interaction, membre: discord.Member):
        await self._do_follow(interaction, membre, "user follow")

    @user.command(name="unfollow", description="Ne plus suivre un membre")
    @app_commands.describe(membre="Membre a ne plus suivre")
    async def unfollow(self, interaction: discord.Interaction, membre: discord.Member):
        if not self._follow_enabled():
            await interaction.response.send_message(
                "Le suivi de membres est désactivé sur ce bot.", ephemeral=True
            )
            await log_command_use(
                self.bot,
                self.bot.config,
                interaction,
                "user unfollow",
                Membre=f"{membre} ({membre.id})",
                Resultat="Desactive",
            )
            return
        follows = load_follows()
        gk = guild_key(interaction.guild.id)
        uk = user_key(interaction.user.id)
        tk = user_key(membre.id)

        if tk not in follows.get(gk, {}).get(uk, []):
            await interaction.response.send_message(f"Tu ne suis pas **{membre.display_name}**.", ephemeral=True)
            await log_command_use(
                self.bot,
                self.bot.config,
                interaction,
                "user unfollow",
                Membre=f"{membre} ({membre.id})",
                Resultat="Pas suivi",
            )
            return

        follows[gk][uk].remove(tk)
        save_follows(follows)
        await interaction.response.send_message(f"Tu ne suis plus **{membre.display_name}**.", ephemeral=True)
        await log_command_use(
            self.bot,
            self.bot.config,
            interaction,
            "user unfollow",
            Membre=f"{membre} ({membre.id})",
            Resultat="Unfollow",
        )

    @user.command(name="following", description="Voir les membres que tu suis")
    async def following(self, interaction: discord.Interaction):
        if not self._follow_enabled():
            await interaction.response.send_message(
                "Le suivi de membres est désactivé sur ce bot.", ephemeral=True
            )
            await log_command_use(
                self.bot, self.bot.config, interaction, "user following", Resultat="Desactive"
            )
            return
        follows = load_follows()
        gk = guild_key(interaction.guild.id)
        uk = user_key(interaction.user.id)
        targets = follows.get(gk, {}).get(uk, [])

        if not targets:
            await interaction.response.send_message("Tu ne suis personne pour l'instant.", ephemeral=True)
            await log_command_use(
                self.bot, self.bot.config, interaction, "user following", Total="0"
            )
            return

        lines = []
        for tid in targets:
            member = interaction.guild.get_member(int(tid))
            lines.append(f"- {member.mention if member else f'`{tid}`'}")

        embed = discord.Embed(title="Membres suivis", color=discord.Color.teal())
        embed.description = "\n".join(lines)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await log_command_use(
            self.bot, self.bot.config, interaction, "user following", Total=str(len(targets))
        )

    @user.command(name="find", description="Trouver où est un membre")
    @app_commands.describe(membre="Membre à localiser")
    async def user_find(self, interaction: discord.Interaction, membre: discord.Member):
        embed = self._build_find_embed(membre)
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await log_command_use(
            self.bot, self.bot.config, interaction, "user find", Membre=f"{membre} ({membre.id})"
        )

    @commands.Cog.listener()
    async def on_presence_update(self, before: discord.Member, after: discord.Member):
        if before.status in (discord.Status.offline, discord.Status.invisible) and after.status in (
            discord.Status.online,
            discord.Status.idle,
            discord.Status.dnd,
        ):
            await self._notify_followers(
                after.guild,
                after,
                f"**{after.display_name}** vient de se connecter ({STATUS_LABELS.get(after.status, 'En ligne')}).",
            )

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        if before.channel is None and after.channel is not None:
            await self._notify_followers(
                member.guild,
                member,
                f"**{member.display_name}** a rejoint {after.channel.mention}.",
            )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        if isinstance(message.author, discord.Member):
            self._record_seen(message.author, message.channel)
            await self._notify_followers(
                message.guild,
                message.author,
                f"**{message.author.display_name}** a envoyé un message dans {message.channel.mention}.",
                cooldown=True,
            )


async def setup(bot):
    await bot.add_cog(Users(bot))
