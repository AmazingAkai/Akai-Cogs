"""
MIT License

Copyright (c) 2023-present AmazingAkai

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
import time
from typing import Annotated, Dict, List, Optional

import aiohttp
import discord
from redbot.cogs.streams import streams
from redbot.cogs.streams.streamtypes import TWITCH_BASE_URL, TWITCH_STREAMS_ENDPOINT
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.views import SimpleMenu

TWITCH_GAMES_ENDPOINT = TWITCH_BASE_URL + "/helix/games"


class FetchError(Exception):
    """Custom exception for fetching errors."""


class GameNotFoundError(FetchError):
    """Exception for game not found errors."""


class StreamFetchError(FetchError):
    """Exception for stream fetch errors."""


class RoleConverter(commands.RoleConverter):
    async def convert(self, ctx: commands.GuildContext, argument: str) -> discord.Role:
        if argument.lower() in ("everyone", "@everyone"):
            return ctx.guild.default_role
        return await super().convert(ctx, argument)


class Stream:
    def __init__(self, data: dict) -> None:
        self.data = data
        self.id: int = int(data["id"])

    def __hash__(self) -> int:
        return hash(self.id)

    def make_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title=self.data["title"],
            description=f"**{self.data['user_name']}** is streaming **{self.data['game_name']}**",
            url=f"https://twitch.tv/{self.data['user_login']}",
            color=discord.Color.purple(),
        )
        embed.set_image(url=self.data["thumbnail_url"].format(width=1280, height=720))
        embed.add_field(
            name="Viewer Count",
            value=f"{self.data['viewer_count']} viewers",
            inline=False,
        )
        embed.add_field(name="Language", value=self.data["language"], inline=False)
        embed.add_field(name="Started At", value=self.data["started_at"], inline=False)
        embed.add_field(
            name="Is Adult Stream?", value=self.data["is_mature"], inline=False
        )
        if self.data["tags"]:
            embed.add_field(
                name="Tags", value=", ".join(self.data["tags"]), inline=False
            )
        return embed


class Game:
    def __init__(self, data: dict, headers: dict) -> None:
        self.data = data
        self.headers = headers
        self.name = self.data["name"]
        self.id: int = int(data["id"])

        self._rate_limit_resets = set()
        self._rate_limit_remaining = (
            800  # Assuming an initial limit of 800 requests per minute
        )

    def __hash__(self) -> int:
        return hash(self.id)

    async def wait_for_rate_limit_reset(self) -> None:
        current_time = int(time.time())
        self._rate_limit_resets = {
            x for x in self._rate_limit_resets if x > current_time
        }

        if self._rate_limit_remaining == 0:
            if self._rate_limit_resets:
                reset_time = next(iter(self._rate_limit_resets))
                wait_time = reset_time - current_time + 0.1
                await asyncio.sleep(wait_time)

    async def fetch_streams(self) -> List[Stream]:
        streams = []

        await self.wait_for_rate_limit_reset()

        async with aiohttp.ClientSession() as session:
            async with session.get(
                TWITCH_STREAMS_ENDPOINT,
                headers=self.headers,
                params={"game_id": self.id, "first": 100},
            ) as response:
                if response.status == 429:
                    reset = response.headers.get("Ratelimit-Reset")
                    if reset:
                        self._rate_limit_resets.add(int(reset))
                    await self.wait_for_rate_limit_reset()

                    return await self.fetch_streams()

                if response.status != 200:
                    raise StreamFetchError(
                        f"Error {response.status} was raised while fetching streams."
                    )

                data = await response.json()
                for stream_data in data.get("data", []):
                    stream = Stream(stream_data)
                    streams.append(stream)

        remaining = response.headers.get("Ratelimit-Remaining")
        if remaining:
            self._rate_limit_remaining = int(remaining)

        reset = response.headers.get("Ratelimit-Reset")
        if reset:
            self._rate_limit_resets.add(int(reset))

        return streams


class GameStreams(commands.Cog):
    """Receive live announcements for new game streams."""

    __version__ = "0.0.1"
    __author__ = "Akai"

    def __init__(self, bot: Red) -> None:
        self.bot = bot

        self.games: Dict[str, Optional[Game]] = {}
        self.streams: Dict[Game, List[Stream]] = {}

        self.config = Config.get_conf(self, identifier=7474034061)
        self.config.register_global(
            alerts=[]
        )  # List of Dict having game_name and alerts (List of dicts having channel_id, guild_id and ping_role_id)

    @property
    def streams_cog(self) -> Optional[streams.Streams]:
        return self.bot.get_cog("Streams")  # type: ignore

    async def check_streams(self):
        if self.streams_cog is None:
            return
        await self.streams_cog.maybe_renew_twitch_bearer_token()
        token = (await self.bot.get_shared_api_tokens("twitch")).get("client_id")
        if token is None:
            return
        access_token = self.streams_cog.ttv_bearer_cache.get("access_token")
        if access_token is None:
            return
        headers = {
            "Client-ID": token,
            "Authorization": f"Bearer {access_token}",
        }

    async def fetch_game(self, game_name: str, headers: dict) -> Game:
        if game_name.lower() in self.games:
            game = self.games[game_name.lower()]
            if game is not None:
                return game

            raise GameNotFoundError("That game does not exist on Twitch.")

        async with aiohttp.ClientSession() as session:
            async with session.get(
                TWITCH_GAMES_ENDPOINT,
                headers=headers,
                params={"name": game_name, "first": 1},
            ) as response:
                if response.status == 401:
                    raise FetchError(
                        "Failed to fetch that game, make sure to set proper credentials. Check `[p]streamset twitchtoken` for more info."
                    )

                data = await response.json()
                games_data = data["data"]
                if not games_data:
                    self.games[game_name.lower()] = None
                    raise GameNotFoundError("That game does not exist on Twitch.")

                game = Game(games_data[0], headers)
                self.games[game_name.lower()] = game
                return game

    @commands.group(name="gamestreams", aliases=["gs", "gamestream"])
    @commands.guild_only()
    async def gamestreams(self, ctx: commands.Context) -> None:
        """Command to announce game streams and search them."""

    @gamestreams.group(name="twitch")
    @commands.guild_only()
    async def gamestreams_twitch(self, ctx: commands.Context) -> None:
        """Command to announce game streams and search them on twitch."""

    @gamestreams_twitch.command(name="search")
    @commands.guild_only()
    @commands.cooldown(rate=1, per=10, type=commands.BucketType.member)
    async def gamestreams_twitch_search(
        self, ctx: commands.GuildContext, *, game_name: str
    ) -> None:
        """Search ongoing streams for a game on Twitch."""
        if self.streams_cog is None:
            await ctx.send(
                f"Streams cog is currently not loaded. {' You can load the cog using `[p]load streams`' if await self.bot.is_owner(ctx.author) else ''}"
            )
            return

        await self.streams_cog.maybe_renew_twitch_bearer_token()
        token = (await self.bot.get_shared_api_tokens("twitch")).get("client_id")

        if token is None:
            await ctx.send(
                "The Twitch Client ID is not set. Please read `;streamset twitchtoken`."
            )
            return

        access_token = self.streams_cog.ttv_bearer_cache.get("access_token")
        if access_token is None:
            await ctx.send("Failed to fetch the access token for Twitch API.")
            return

        headers = {
            "Client-ID": token,
            "Authorization": f"Bearer {access_token}",
        }

        try:
            game = await self.fetch_game(game_name, headers)
        except Exception as error:
            await ctx.send(str(error))
            return

        try:
            streams = await game.fetch_streams()
        except StreamFetchError as error:
            await ctx.send(str(error))
            return

        if not streams:
            await ctx.send("No streams found for this game.")
            return

        embeds: List[discord.Embed] = []

        for i, stream in enumerate(streams):
            embed = stream.make_embed()
            embed.set_footer(
                text=f"Page {i + 1}/{len(streams)}",
                icon_url=ctx.guild.icon or self.bot.user.display_avatar,  # type: ignore
            )
            embeds.append(embed)

        pages = SimpleMenu(embeds, disable_after_timeout=True)  # type: ignore

        await pages.start(ctx)

    @gamestreams_twitch.command(name="alert")
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    @commands.cooldown(rate=1, per=10, type=commands.BucketType.member)
    async def gamestreams_twitch_alert(
        self,
        ctx: commands.GuildContext,
        channel: Optional[discord.TextChannel] = None,
        ping_role: Optional[Annotated[discord.Role, RoleConverter]] = None,
        *,
        game_name: str,
    ) -> None:
        """Search ongoing streams for a game on Twitch."""
        if self.streams_cog is None:
            await ctx.send(
                f"Streams cog is currently not loaded. {' You can load the cog using `[p]load streams`' if await self.bot.is_owner(ctx.author) else ''}"
            )
            return

        if channel is None:
            if not isinstance(ctx.channel, discord.TextChannel):
                await ctx.send("Announcements channel must be a text channel.")
                return
            channel = ctx.channel

        await self.streams_cog.maybe_renew_twitch_bearer_token()
        token = (await self.bot.get_shared_api_tokens("twitch")).get("client_id")

        if token is None:
            await ctx.send(
                "The Twitch Client ID is not set. Please read `;streamset twitchtoken`."
            )
            return

        access_token = self.streams_cog.ttv_bearer_cache.get("access_token")
        if access_token is None:
            await ctx.send("Failed to fetch the access token for Twitch API.")
            return

        headers = {
            "Client-ID": token,
            "Authorization": f"Bearer {access_token}",
        }

        try:
            game = await self.fetch_game(game_name, headers)
        except Exception as error:
            await ctx.send(str(error))
            return

        alerts = await self.config.alerts()

        removed = False

        for alert in alerts:
            if alert["game"] == game.name.lower():
                for game_alert in alert["alerts"]:
                    if (
                        game_alert["guild_id"] == ctx.guild.id
                        and game_alert["channel_id"] == channel.id
                    ):
                        alert["alerts"].remove(game_alert)
                        removed = True
                        break
                else:
                    alert["alerts"].append(
                        {
                            "guild_id": ctx.guild.id,
                            "channel_id": channel.id,
                            "ping_role_id": ping_role.id if ping_role else None,
                        }
                    )
                break
        else:
            alerts.append(
                {
                    "game": game.name.lower(),
                    "alerts": [
                        {
                            "guild_id": ctx.guild.id,
                            "channel_id": channel.id,
                            "ping_role_id": ping_role.id if ping_role else None,
                        }
                    ],
                }
            )

        await self.config.alerts.set(alerts)

        message = (
            f"Successfully {'removed' if removed else 'added'} alert for `{game.name}` "
            f"to {channel.mention}."
        )
        await ctx.reply(message, mention_author=False)
