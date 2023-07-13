"""
MIT License

Copyright (c) 2022-present ltzmax

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
import asyncio
import contextlib
import random
from typing import Optional, Set, Union

import discord
from redbot.core import app_commands, commands
from redbot.core.bot import Red


class GuessTheNumber(commands.Cog):
    __version__ = "0.0.1"
    __author__ = "Akai"

    def __init__(self, bot: Red):
        self.bot = bot

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad!"""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: {self.__author__}\nCog Version: {self.__version__}"

    @commands.hybrid_command(
        name="guessthenumber",
        aliases=["gtn", "guess_the_number"],
        cooldown_after_parsing=True,
    )
    @commands.max_concurrency(1, per=commands.BucketType.channel)
    @commands.cooldown(1, 60, commands.BucketType.channel)
    @commands.guild_only()
    @app_commands.describe(
        lower_limit="The minimum value for the randomly chosen number.",
        higher_limit="The maximum value for the randomly chosen number.",
        hints="Indicates whether to provide hints with reactions for higher or lower guesses.",
        dm_number="Specifies if the number should be sent to the host via direct message.",
    )
    async def guess_the_number(
        self,
        ctx: commands.GuildContext,
        lower_limit: int = 0,
        higher_limit: int = 100,
        hints: bool = False,
        dm_number: bool = False,
    ):
        """Starts a "Guess the Number" game in the current channel."""
        if lower_limit >= higher_limit:
            return await ctx.send(
                "Error: The lower limit must be less than the higher limit."
            )

        # Restrict the limits to a particular value
        lower_limit = max(lower_limit, 0)
        higher_limit = min(higher_limit, 1000000)

        number = random.randint(lower_limit, higher_limit)
        guess = -1

        num_guesses = 0

        def check(message):
            return ctx.channel == message.channel

        players: Set[Union[discord.Member, discord.User]] = {ctx.author}
        last_player: Optional[Union[discord.Member, discord.User]] = None

        if dm_number:
            try:
                await ctx.author.send(f"The random number is `{number}`!")
            except discord.HTTPException:
                pass

        await ctx.send(
            f"Guess a number between `{lower_limit}` and `{higher_limit}`. Good Luck!"
        )
        while guess != number:
            try:
                guess_message: discord.Message = await self.bot.wait_for(
                    "message", check=check, timeout=60.0
                )
                guess = int(guess_message.content)
            except asyncio.TimeoutError:
                return await ctx.send("Time's up! You took too long to guess.")
            except ValueError:
                continue
            else:
                last_player = guess_message.author
                players.add(guess_message.author)
                num_guesses += 1
                if hints:
                    # fmt: off
                    with contextlib.suppress(discord.HTTPException):
                        if guess > number:
                            await guess_message.add_reaction("\N{UPWARDS BLACK ARROW}")
                        elif guess == number:
                            await guess_message.add_reaction("\N{BALLOT BOX WITH CHECK}")
                        else:
                            await guess_message.add_reaction("\N{DOWNWARDS BLACK ARROW}")
                    # fmt: on

        embed = discord.Embed(
            title="Guess the Number Game",
            description="Congratulations, you guessed it!",
            color=discord.Color.green(),
        )
        if last_player:  # Should never evaluate to False
            embed.set_thumbnail(url=last_player.display_avatar)

        embed.add_field(
            name="Winner",
            value=f"{last_player.mention if last_player else 'None'}",
            inline=False,
        )
        embed.add_field(name="Guessed Number", value=str(guess), inline=False)
        embed.add_field(name="Number of Guesses", value=str(num_guesses), inline=False)
        embed.add_field(name="Number of Players", value=str(len(players)), inline=False)
        await ctx.send(embed=embed)
