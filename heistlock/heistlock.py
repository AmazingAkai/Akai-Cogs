import asyncio
import copy
from typing import Dict, Optional, Sequence

import discord
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import bold

DANK_MEMER_ID = 270904126974590976


class RoleListConverter(commands.Converter):
    async def convert(
        self, ctx: commands.Context, argument: str
    ) -> Sequence[discord.Role]:
        roles: Sequence[discord.Role] = []

        for role_str in argument.split():
            role = await commands.RoleConverter().convert(ctx, role_str.strip())
            roles.append(role)

        return roles


class HeistLockFlags(commands.FlagConverter, prefix="--", delimiter=" "):
    roles: Sequence[discord.Role] = commands.flag(
        description="Roles for which command will unviewlock the channel.",
        converter=RoleListConverter,
    )
    members_role: Optional[discord.Role] = commands.flag(
        description="Role for which command will viewlock the channel, defaults to '@everyone'.",
        default=None,
    )
    viewlock_before_start: bool = commands.flag(
        description="Whether to viewlock the channel before heist start, defaults to 'False'.",
        default=False,
    )


class HeistLock(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot

    @commands.has_permissions(manage_guild=True)
    @commands.bot_has_permissions(manage_channels=True)
    @commands.max_concurrency(1, per=commands.BucketType.guild)
    @commands.hybrid_command(aliases=["hstart", "heiststart", "hlock"])
    async def heistlock(self, ctx: commands.Context, *, flags: HeistLockFlags):
        """This command will unviewlock the channel for the given roles on starting heist.

        **Flags:**
        `--roles`: Roles for which command will unviewlock the channel.
        `--members_role`: Role for which command will viewlock the channel, defaults to '@everyone'.
        `--viewlock_before_start`: Whether to viewlock the channel before heist start, defaults to 'False'.
        """

        if not isinstance(ctx.channel, discord.TextChannel):
            return await ctx.send("This command can only be used in text channels.")
        if not flags.roles:
            return await ctx.send("Please mention atleast one role.")
        if len(flags.roles) > 5:
            return await ctx.send("Please mention no more than 5 roles.")

        assert ctx.guild is not None

        members_role = flags.members_role or ctx.guild.default_role
        color = await ctx.bot.get_embed_color(ctx)

        if flags.viewlock_before_start:
            embed = discord.Embed(
                title="Heist Start",
                description="Please run the heist command in this channel. "
                f"The channel has been viewlocked for {', '.join(role.mention for role in flags.roles)}.",
                color=color,
            )

        else:
            embed = discord.Embed(
                title="Listening for Heist Start",
                description="Please run the heist command in this channel. "
                f"The channel will be unviewlocked for {', '.join(role.mention for role in flags.roles)}.",
                color=color,
            )

        await ctx.send(embed=embed)

        def is_heiststart_message(message: discord.Message) -> bool:
            return (
                bool(message.embeds)
                and bool(message.embeds[0].description)
                and message.embeds[0].description.startswith(
                    f"They're trying to break into {bold('server')}'s bank!"
                )
                and message.author.id == DANK_MEMER_ID
                and message.channel.id == ctx.channel.id
            )

        def is_heistend_message(message: discord.Message) -> bool:
            return (
                bool(message.embeds)
                and bool(message.embeds[0].description)
                and message.embeds[0].description.startswith(
                    "Amazing job everybody, we racked up a total of"
                )
                and message.author.id == DANK_MEMER_ID
                and message.channel.id == ctx.channel.id
            )

        if not flags.viewlock_before_start:
            try:
                await self.bot.wait_for(
                    "message", check=is_heiststart_message, timeout=60
                )
            except asyncio.TimeoutError:
                return await ctx.send("Timed out waiting for heist start message.")

        before = await self.update_channel(ctx, flags.roles, members_role)

        embed = discord.Embed(
            title="Heist Started",
            description="The heist has started. Channel has been unviewlocked "
            f"for {', '.join(role.mention for role in flags.roles)}.",
            color=color,
        )

        await ctx.send(embed=embed)

        try:
            await self.bot.wait_for("message", check=is_heistend_message, timeout=300)
        except asyncio.TimeoutError:
            return await ctx.send("Timed out waiting for heist end message.")
        finally:
            await self.update_channel(ctx, flags.roles, members_role, before=before)

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
        ret[members_role] = copy.deepcopy(overwrites)
        overwrites.view_channel = before[members_role].view_channel if before else False
        await ctx.channel.set_permissions(members_role, overwrite=overwrites)

        for role in roles:
            overwrites = ctx.channel.overwrites_for(role)
            ret[role] = copy.deepcopy(overwrites)
            overwrites.view_channel = before[role].view_channel if before else True
            await ctx.channel.set_permissions(role, overwrite=overwrites)

        return ret
