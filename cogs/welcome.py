import discord
from discord.ext import commands

from utils.helpers import log_embed, send_log


class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        welcome_cfg = self.config.get("welcome", {})
        channel_id = self.config.get("welcome_channel_id")

        if channel_id:
            channel = member.guild.get_channel(channel_id)
            if channel:
                msg = welcome_cfg.get(
                    "message",
                    "🎉 Bienvenue {member} sur **{server}** ! Tu es le **{count}**ème membre.",
                )
                text = msg.format(
                    member=member.mention,
                    server=member.guild.name,
                    count=member.guild.member_count,
                )
                await channel.send(text)

        dm_msg = welcome_cfg.get("dm_message")
        if dm_msg:
            try:
                await member.send(dm_msg.format(server=member.guild.name))
            except discord.HTTPException:
                pass

        embed = log_embed(
            "🎉 Arrivée",
            discord.Color.green(),
            Membre=f"{member} ({member.id})",
            Compte=f"Créé le {discord.utils.format_dt(member.created_at, 'R')}",
            Total=str(member.guild.member_count),
        )
        await send_log(self.bot, self.config, embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        goodbye_cfg = self.config.get("goodbye", {})
        channel_id = self.config.get("goodbye_channel_id")

        if channel_id:
            channel = member.guild.get_channel(channel_id)
            if channel:
                msg = goodbye_cfg.get(
                    "message",
                    "👋 Au revoir **{member}**, on espère te revoir bientôt !",
                )
                await channel.send(msg.format(member=member.display_name))

        embed = log_embed(
            "👋 Départ",
            discord.Color.light_grey(),
            Membre=f"{member} ({member.id})",
            Total=str(member.guild.member_count),
        )
        await send_log(self.bot, self.config, embed)


async def setup(bot):
    await bot.add_cog(Welcome(bot))
