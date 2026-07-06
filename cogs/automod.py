import re
from collections import defaultdict
from datetime import datetime, timedelta

import discord
from discord.ext import commands

from utils.helpers import has_bypass, is_moderator, log_embed, send_log


class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config
        self.message_history = defaultdict(list)

    def _automod_cfg(self):
        return self.config.get("automod", {})

    def _contains_link(self, content: str) -> bool:
        pattern = r"(https?://|www\.|discord\.gg/|discord\.com/invite/)"
        return bool(re.search(pattern, content, re.IGNORECASE))

    def _contains_insult(self, content: str) -> bool:
        words = self._automod_cfg().get("insult_words", [])
        lower = content.lower()
        return any(word.lower() in lower for word in words)

    def _is_spam(self, user_id: int) -> bool:
        cfg = self._automod_cfg()
        threshold = cfg.get("spam_threshold", 5)
        interval = cfg.get("spam_interval_seconds", 5)
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=interval)

        history = self.message_history[user_id]
        history[:] = [t for t in history if t > cutoff]
        history.append(now)
        return len(history) >= threshold

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        if isinstance(message.author, discord.Member) and (has_bypass(message.author, self.config) or is_moderator(message.author)):
            return

        cfg = self._automod_cfg()
        reason = None

        if cfg.get("anti_spam") and self._is_spam(message.author.id):
            reason = "Anti-spam : trop de messages envoyés rapidement"

        if not reason and cfg.get("anti_links") and self._contains_link(message.content):
            reason = "Anti-liens : liens non autorisés"

        if not reason and cfg.get("anti_insults") and self._contains_insult(message.content):
            reason = "Anti-insultes : langage inapproprié"

        if reason:
            try:
                await message.delete()
            except discord.HTTPException:
                pass

            try:
                await message.channel.send(
                    f"{message.author.mention}, message supprime : {reason}",
                    delete_after=5,
                )
            except discord.HTTPException:
                pass

            embed = log_embed(
                "Auto-moderation",
                discord.Color.dark_red(),
                Membre=f"{message.author} ({message.author.id})",
                Salon=f"{message.channel.mention}",
                Raison=reason,
                Contenu=message.content[:1000] or "*vide*",
            )
            await send_log(self.bot, self.config, embed)


async def setup(bot):
    await bot.add_cog(AutoMod(bot))
