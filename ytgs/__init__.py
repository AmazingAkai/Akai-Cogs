from redbot.core.bot import Red

from .ytgs import YTGS


async def setup(bot: Red) -> None:
    await bot.add_cog(YTGS(bot))
