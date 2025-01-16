from __future__ import annotations

import asyncio
import copy
from typing import TYPE_CHECKING, Optional, Sequence

import discord
from redbot.core import commands
from redbot.core.bot import Red

if TYPE_CHECKING:
    from typing import Dict, Union

    CHANNEL_OVERWRITES = Dict[
        Union[discord.Member, discord.Role, discord.Object], discord.PermissionOverwrite
    ]

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
        """

        if not isinstance(ctx.channel, discord.TextChannel):
            return await ctx.send("This command can only be used in text channels.")
        if not flags.roles:
            return await ctx.send("Please mention atleast one role.")
        if len(flags.roles) > 5:
            return await ctx.send("Please mention no more than 5 roles.")

        def is_heistend_message(message: discord.Message) -> bool:
            return (
                bool(message.embeds)
                and bool(message.embeds[0].description)
                and (
                    message.embeds[0].description.startswith(
                        "Amazing job everybody, we racked up a total of"
                    )
                    or message.embeds[0].description
                    == "Server is not popular enough and didn't get enough people to rob its bank."
                )
                and message.author.id == DANK_MEMER_ID
                and message.channel.id == ctx.channel.id
            )

        assert ctx.guild is not None

        members_role = flags.members_role or ctx.guild.default_role
        color = await ctx.bot.get_embed_color(ctx)

        before = await self.update_channel(ctx, flags.roles, members_role)

        embed = discord.Embed(
            title="Heist Lock",
            description=f"Channel has been viewlocked for {members_role.mention} and unviewlocked "
            f"for {', '.join(role.mention for role in flags.roles)}.",
            color=color,
        )

        await ctx.send(embed=embed)

        try:
            await self.bot.wait_for("message", check=is_heistend_message, timeout=360)
        except asyncio.TimeoutError:
            return await ctx.send("Timed out waiting for heist end message.")
        finally:
            await ctx.channel.edit(
                overwrites=before, reason="Heist lock over. Permissions reset."
            )

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
    ) -> CHANNEL_OVERWRITES:
        assert isinstance(ctx.channel, discord.TextChannel)

        before = {obj: overwrites for obj, overwrites in ctx.channel.overwrites.items()}
        permissions = {
            obj: copy.deepcopy(overwrites)
            for obj, overwrites in ctx.channel.overwrites.items()
        }

        overwrites = permissions.get(members_role) or discord.PermissionOverwrite()
        overwrites.view_channel = False
        permissions[members_role] = overwrites

        for role in roles:
            overwrites = permissions.get(role) or discord.PermissionOverwrite()
            overwrites.view_channel = True
            permissions[role] = overwrites

        await ctx.channel.edit(
            overwrites=permissions,
            reason=f"Heist lock initiated by {ctx.author.display_name} ({ctx.author.id})",
        )

        return before
