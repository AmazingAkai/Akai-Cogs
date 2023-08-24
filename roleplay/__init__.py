from redbot.core.bot import Red

from .roleplay import RolePlay

__red_end_user_data_statement__ = (
    "This cog does not persistently store data about users."
)


async def setup(bot: Red):
    command = bot.get_command("hug")
    if command is not None:
        bot.remove_command("hug")
    await bot.add_cog(RolePlay(bot, command))
