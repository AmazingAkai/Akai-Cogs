import discord
from redbot.core import commands
from redbot.core.bot import Red


class HeistLock(commands.Cog):
    def __init__(self, bot: Red):
        self.bot = bot

    @commands.has_guild_permissions(manage_guild=True)
    @commands.hybrid_command()
    async def heistlock(
        self,
        ctx: commands.Context,
        roles: commands.Greedy[discord.Role],
    ):
        """This command does nothing."""
        await ctx.send(f"Got roles {', '.join(role.mention for role in roles)}")
