import asyncio
from typing import Dict, Optional, Sequence

import discord
from redbot.core import app_commands, commands
from redbot.core.bot import Red

DANK_MEMER_ID = 270904126974590976


class HeistLock(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot

    @commands.has_permissions(manage_guild=True)
    @commands.bot_has_permissions(manage_channels=True)
    @commands.max_concurrency(1, per=commands.BucketType.guild)
    @commands.hybrid_command(aliases=["hstart", "heiststart", "hlock"])
    @app_commands.describe(
        roles="The roles for which command will unlock the channel.",
        members_role="The role for which command will lock the channel, defaults to '@everyone'.",
    )
    async def heistlock(
        self,
        ctx: commands.Context,
        roles: commands.Greedy[discord.Role],
        members_role: Optional[discord.Role] = None,
    ):
        """This command will unlock the channel for the given roles on starting heist."""

        if not isinstance(ctx.channel, discord.TextChannel):
            return await ctx.send("This command can only be used in text channels.")
        if not roles:
            return await ctx.send("Please mention atleast one role.")
        if len(roles) > 5:
            return await ctx.send("Please mention no more than 5 roles.")

        assert ctx.guild is not None

        members_role = members_role or ctx.guild.default_role
        color = await ctx.bot.get_embed_color(ctx)

        embed = discord.Embed(
            title="Listening for Heist Start",
            description="Please run the heist command in this channel.",
            color=color,
        )

        await ctx.send(embed=embed)

        def is_heiststart_message(message: discord.Message) -> bool:
            return (
                bool(message.embeds)
                and bool(message.embeds[0].description)
                and message.embeds[0].description.startswith(
                    "They're trying to break into **server**'s bank!"
                )
                and message.author.id == DANK_MEMER_ID
                and message.channel.id == ctx.channel.id
            )

        try:
            await self.bot.wait_for("message", check=is_heiststart_message, timeout=60)
        except asyncio.TimeoutError:
            return await ctx.send("Timed out waiting for heist start message.")

        before = await self.update_channel(ctx, roles, members_role)

        embed = discord.Embed(
            title="Heist Started",
            description="The heist has started. Channel has been unlocked for given roles.",
            color=color,
        )

        await ctx.send(embed=embed)

        await asyncio.sleep(95)  # Heist ends in ~95 seconds.

        await self.update_channel(ctx, roles, members_role, before=before)

        embed = discord.Embed(
            title="Heist Ended",
            description="The heist has ended. Channel permissions have been reset.",
            color=color,
        )

        await ctx.send(embed=embed)

    async def update_channel(
        self,
        ctx: commands.Context,
        roles: Sequence[discord.Role],
        members_role: discord.Role,
        before: Optional[Dict[discord.Role, discord.PermissionOverwrite]] = None,
    ) -> Dict[discord.Role, discord.PermissionOverwrite]:
        assert isinstance(ctx.channel, discord.TextChannel)

        ret: Dict[discord.Role, discord.PermissionOverwrite] = {}

        overwrites = ctx.channel.overwrites_for(members_role)
        ret[members_role] = overwrites
        overwrites.view_channel = before[members_role].view_channel if before else False
        await ctx.channel.set_permissions(members_role, overwrite=overwrites)

        for role in roles:
            overwrites = ctx.channel.overwrites_for(role)
            ret[role] = overwrites
            overwrites.view_channel = before[role].view_channel if before else True
            await ctx.channel.set_permissions(role, overwrite=overwrites)

        return ret
