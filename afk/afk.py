"""
MIT License

Copyright (c) 2023-present Akai

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from __future__ import annotations

import asyncio
import contextlib
import time
from typing import TYPE_CHECKING, Optional

import discord
from redbot.core import Config, commands
from redbot.core.utils.views import SimpleMenu

if TYPE_CHECKING:
    from typing import Sequence

    from discord.abc import MessageableChannel


class InteractionSimpleMenu(SimpleMenu):
    async def start(
        self,
        interaction: discord.Interaction,
        *,
        user: Optional[discord.abc.User] = None,
        ephemeral: bool = False,
    ):
        self.author = user or interaction.user
        kwargs = await self.get_page(self.current_page)
        self.message = await interaction.response.send_message(
            **kwargs,  # type: ignore
            ephemeral=ephemeral,
        )


class ViewMentionsView(discord.ui.View):
    message: discord.Message

    def __init__(self, embeds: Sequence[discord.Embed], author: discord.Member):
        super().__init__(timeout=180)
        self.embeds = embeds
        self.author = author

    @discord.ui.button(label="View Mentions", style=discord.ButtonStyle.green)
    async def view_mentions(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        menus = InteractionSimpleMenu(pages=self.embeds, timeout=180)  # type: ignore
        await menus.start(interaction, ephemeral=True)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.author:
            await interaction.response.defer()
            return False
        return True

    async def on_timeout(self) -> None:
        self.view_mentions.disabled = True
        await self.message.edit(view=self)


class AwayFromKeyboard(commands.Cog):
    """Make the bot send a message whenever you are away from the keyboard."""

    __version__ = "1.1.0"
    __author__ = "Akai"

    def __init__(self, bot):
        self.bot = bot

        self.grace_period = []

        self.config = Config.get_conf(self, identifier=4654651557)

        default_member = {
            "afk": False,
            "mentions": [],
            "afk_since": None,
            "message": None,
        }

        self.config.register_member(**default_member)

        default_guild = {
            "blacklisted_channels": [],
        }

        self.config.register_guild(**default_guild)

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    async def add_afk_to_nickname(self, member: discord.Member) -> None:
        name = member.display_name
        new_name = "[AFK] " + name
        try:
            await member.edit(nick=new_name, reason="User went AFK.")
        except discord.HTTPException:
            pass

    async def remove_afk_from_nickname(self, member: discord.Member) -> None:
        if "[AFK]" in member.display_name:
            try:
                await member.edit(
                    nick=member.display_name.replace("[AFK]", ""),
                    reason="User removed AFK status.",
                )
            except discord.HTTPException:
                pass

    async def remove_afk(
        self, channel: MessageableChannel, member: discord.Member
    ) -> None:
        mentions = await self.config.member(member).mentions()

        await self.config.member(member).clear()
        await self.remove_afk_from_nickname(member)

        embeds = []
        description = f"While you were AFK, you got **{len(mentions)}** ping(s):"
        for i, mentions in enumerate(discord.utils.as_chunks(mentions, 15)):
            for mention in mentions:
                description += f"\n・{mention['author']}・<t:{mention['timestamp']}:R>・[Jump]({mention['url']})"
            embed = discord.Embed(
                title=f"Welcome back, {member.name}" if i == 0 else "",
                description=description,
                color=0x2B2D31,
            )

            description = ""  # clearing description before next chunk
            embeds.append(embed)

        with contextlib.suppress(discord.HTTPException):
            embed = discord.Embed(
                title=f"Welcome back, {member.name}",
                description=f"While you were AFK, you got **{len(mentions)}** pings.",
                color=0x2B2D31,
            )
            view = ViewMentionsView(embeds, member) if embeds else discord.ui.View()
            view.message = await channel.send(embed=embed, view=view)  # type: ignore

    @commands.Cog.listener("on_message_without_command")
    async def afk_listener(self, message: discord.Message) -> None:
        if not message.guild or message.author.bot:
            return

        assert isinstance(message.author, discord.Member)

        cog_disabled = await self.bot.cog_disabled_in_guild(self, message.guild)
        if cog_disabled:
            return

        if message.channel.id in (
            await self.config.guild(message.guild).blacklisted_channels()
        ):
            return

        member_data = await self.config.member(message.author).all()
        if member_data["afk"]:
            if message.author.id not in self.grace_period:
                await self.remove_afk(message.channel, message.author)

        for member in message.mentions:
            if not isinstance(
                member, discord.Member
            ):  # Mentioned member is not in the guild.
                continue

            member_data = await self.config.member(member).all()
            if member_data and member_data["afk"]:
                await message.channel.send(
                    f"{member.name} is AFK: {member_data['message'] or 'No Message'} (since <t:{member_data['afk_since']}:R>)",
                    delete_after=5,
                )
                if message.channel.permissions_for(member).read_messages is True:
                    config = self.config.member(member)

                    async with config.mentions() as mentions:
                        new_mention = {
                            "author": message.author.name,
                            "timestamp": int(time.time()),
                            "url": message.jump_url,
                        }
                        mentions.append(new_mention)

    @commands.guild_only()
    @commands.hybrid_command(aliases=["away", "touchgrass"])
    @commands.cooldown(1, 5.0, commands.BucketType.member)
    async def afk(self, ctx: commands.GuildContext, *, message: Optional[str] = None):
        """Make the bot send a message whenever you are away from the keyboard."""

        data = await self.config.member(ctx.author).all()
        if data and data["afk"]:
            await self.remove_afk(ctx.channel, ctx.author)
        else:
            user_data = {
                "afk": True,
                "mentions": [],
                "afk_since": int(time.time()),
                "message": message,
            }
            await self.config.member(ctx.author).set(user_data)

            embed = discord.Embed(
                description=f"✅ I set your AFK: {message or 'No Message'}",
                color=0x2B2D31,
            )

            await self.add_afk_to_nickname(ctx.author)

            await ctx.send(embed=embed)

            # Cooldown feature added.
            self.grace_period.append(ctx.author.id)
            await asyncio.sleep(5)
            self.grace_period.remove(ctx.author.id)

    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    @commands.hybrid_group(name="afkset", aliases=["awayset"])
    async def afkset(self, ctx: commands.Context) -> None:
        """Set and manage afk command."""

    @afkset.group(name="blacklist", aliases=["bl"])  # type: ignore
    async def afkset_blacklist(self, ctx: commands.Context) -> None:
        """Set the blacklist channel to ignore AFK."""

    @afkset_blacklist.command(name="add", aliases=["a", "+"])
    async def afkset_blacklist_add(
        self, ctx: commands.GuildContext, channel: discord.TextChannel
    ) -> None:
        """Add a blacklist channel to ignore AFK."""
        channel_ids = await self.config.guild(ctx.guild).blacklisted_channels()
        if channel.id in channel_ids:
            await ctx.message.add_reaction("❎")
        else:
            config = self.config.guild(ctx.guild)
            async with config.blacklisted_channels() as blacklisted_channels:
                blacklisted_channels.append(channel.id)
            await ctx.message.add_reaction("✅")

    @afkset_blacklist.command(name="remove", aliases=["r", "-"])
    async def afkset_blacklist_remove(
        self, ctx: commands.GuildContext, channel: discord.TextChannel
    ) -> None:
        """Remove a blacklist channel from ignoring AFK."""
        channel_ids = await self.config.guild(ctx.guild).blacklisted_channels()
        if channel.id not in channel_ids:
            await ctx.message.add_reaction("❎")
        else:
            config = self.config.guild(ctx.guild)
            async with config.blacklisted_channels() as blacklisted_channels:
                blacklisted_channels.remove(channel.id)
            await ctx.message.add_reaction("✅")

    @afkset_blacklist.command(name="list")
    async def afkset_blacklist_list(self, ctx: commands.GuildContext) -> None:
        """Get the list of channels where AFK is ignored."""
        channel_ids = await self.config.guild(ctx.guild).blacklisted_channels()
        description = ""
        for i, channel_id in enumerate(channel_ids):
            description += f"{i+1}. <#{channel_id}>.\n"

        embed = discord.Embed(
            title="Blacklisted Channels", description=description, color=0x2B2D31
        )
        await ctx.send(embed=embed)
