from redbot.core.bot import Red

from .heistlock import HeistLock


async def setup(bot: Red):
    await bot.add_cog(HeistLock(bot))
