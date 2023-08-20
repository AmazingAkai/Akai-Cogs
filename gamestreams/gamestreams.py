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
import datetime
import logging
import time
from typing import Annotated, Any, Dict, List, Optional, Tuple

import aiohttp
import discord
from discord.ext import tasks
from iso639 import NonExistentLanguageError, to_name
from redbot.cogs.streams.streams import Streams
from redbot.cogs.streams.streamtypes import TWITCH_BASE_URL, TWITCH_STREAMS_ENDPOINT
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.views import SimpleMenu

TWITCH_GAMES_ENDPOINT = TWITCH_BASE_URL + "/helix/games"


log = logging.getLogger("akaicogs.gamestreams")


class FetchError(Exception):
    """Custom exception for fetching errors."""


class GameNotFoundError(FetchError):
    """Exception for game not found errors."""


class StreamFetchError(FetchError):
    """Exception for stream fetch errors."""


class RoleConverter(commands.RoleConverter):
    async def convert(
        self, ctx: commands.GuildContext, argument: str
    ) -> Optional[discord.Role]:
        if argument.lower() in ("everyone", "@everyone"):
            return ctx.guild.default_role
        if argument.lower().strip() == "none":
            return None
        return await super().convert(ctx, argument)


class Stream:
    def __init__(self, game: Game, data: dict) -> None:
        self.game = game
        self.data = data

        self.id: int = int(data["id"])
        self.title: str = data["title"]
        self.user_name: str = data["user_name"]
        self.user_login: str = data["user_login"]
        self.game_name: str = data["game_name"]
        self.image: str = data["thumbnail_url"].format(width=1280, height=720)
        self.viewer_count: int = data["viewer_count"]

        try:
            self.language: str = to_name(data["language"])
        except NonExistentLanguageError:
            self.language: str = data["language"]

        self.started_at: datetime.datetime = datetime.datetime.strptime(
            data["started_at"], "%Y-%m-%dT%H:%M:%SZ"
        ).replace(tzinfo=datetime.timezone.utc)
        self.is_mature: bool = data["is_mature"]
        self.tags: List[str] = data["tags"]

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: Stream) -> bool:
        return self.id == other.id

    def make_embed(self) -> discord.Embed:
        embed = discord.Embed(
            title=self.title,
            description=f"**{self.user_name}** is streaming **{self.game_name}**",
            url=f"https://twitch.tv/{self.user_login}",
            color=discord.Color.purple(),
        )

        embed.set_image(url=self.image)
        embed.set_thumbnail(url=self.game.image)

        embed.add_field(
            name="Viewer Count",
            value=f"{self.viewer_count} viewers",
            inline=False,
        )
        embed.add_field(name="Language", value=self.language, inline=False)
        embed.add_field(
            name="Started",
            value=f"{discord.utils.format_dt(self.started_at, style='R')} ({discord.utils.format_dt(self.started_at)})",
            inline=False,
        )
        embed.add_field(
            name="Is Adult Stream?",
            value="Yes" if self.is_mature else "No",
            inline=False,
        )
        if self.tags:
            embed.add_field(name="Tags", value=", ".join(self.tags), inline=False)
        return embed


class Game:
    _rate_limit_resets = set()
    _rate_limit_remaining = 800  # Assuming an initial limit of 800 requests per minute

    def __init__(self, data: dict, headers: dict) -> None:
        self.data = data
        self.headers = headers

        self.name = self.data["name"]
        self.id: int = int(data["id"])
        self.image: str = data["box_art_url"].format(width=180, height=180)

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: Game) -> bool:
        return self.id == other.id

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

    async def fetch_streams(self, cursor: Optional[str] = None) -> List[Stream]:
        streams: List[Stream] = []

        await self.wait_for_rate_limit_reset()

        async with aiohttp.ClientSession() as session:
            params: Dict[str, Any] = {"game_id": self.id, "first": 100, "type": "live"}
            if cursor:
                params["after"] = cursor

            async with session.get(
                TWITCH_STREAMS_ENDPOINT,
                headers=self.headers,
                params=params,
            ) as response:
                if response.status == 429:
                    reset = response.headers.get("Ratelimit-Reset")
                    if reset:
                        self._rate_limit_resets.add(int(reset))
                    await self.wait_for_rate_limit_reset()

                    # Retry the request with the same cursor
                    return await self.fetch_streams(cursor=cursor)

                if response.status != 200:
                    raise StreamFetchError(
                        f"Error {response.status} was raised while fetching streams."
                    )

                data = await response.json()
                for stream_data in data.get("data", []):
                    stream = Stream(self, stream_data)
                    streams.append(stream)

                # Check if there's more data to fetch
                next_cursor = data.get("pagination", {}).get("cursor")
                if next_cursor:
                    # Recursively fetch more streams with the next cursor
                    more_streams = await self.fetch_streams(cursor=next_cursor)
                    streams.extend(more_streams)

            remaining = response.headers.get("Ratelimit-Remaining")
            if remaining:
                self._rate_limit_remaining = int(remaining)

            reset = response.headers.get("Ratelimit-Reset")
            if reset:
                self._rate_limit_resets.add(int(reset))

        return sorted(streams, key=lambda stream: stream.viewer_count, reverse=True)


class GameStreams(commands.Cog):
    """Receive live announcements for new game streams."""

    __version__ = "0.0.1"
    __author__ = "Akai"

    def __init__(self, bot: Red) -> None:
        self.bot = bot

        self.games: Dict[str, Optional[Game]] = {}

        self.config = Config.get_conf(self, identifier=7474034061)
        self.config.register_global(alerts=[])

        self.monitored_games: Dict[Game, List[Stream]] = {}

        self.check_streams.start()

    @property
    def streams_cog(self) -> Optional[Streams]:
        return self.bot.get_cog("Streams")  # type: ignore

    def cog_unload(self):
        self.check_streams.cancel()

    async def fetch_game_headers(self):
        if not self.streams_cog:
            return None

        await self.streams_cog.maybe_renew_twitch_bearer_token()
        token = (await self.bot.get_shared_api_tokens("twitch")).get("client_id")

        if token is None:
            return None

        access_token = self.streams_cog.ttv_bearer_cache.get("access_token")

        if access_token is None:
            return None

        headers = {
            "Client-ID": token,
            "Authorization": f"Bearer {access_token}",
        }

        return headers

    async def process_game_alert(
        self, game_alert: dict, headers: dict
    ) -> Optional[Tuple[List[Stream], List[dict]]]:
        game_name = game_alert["game"]
        game = await self.fetch_game(game_name, headers=headers)
        alerts = game_alert["alerts"]
        streams = await game.fetch_streams()

        if game in self.monitored_games.keys():
            new_streams = [
                stream for stream in streams if not stream in self.monitored_games[game]
            ]
            self.monitored_games[game] = streams
            return new_streams, alerts
        else:
            self.monitored_games[game] = streams
            return [], alerts

    @tasks.loop(minutes=5)
    async def check_streams(self):
        if self.streams_cog is None:
            return

        headers = await self.fetch_game_headers()
        if headers is None:
            return

        game_alerts = await self.config.alerts()
        self.last_checked = datetime.datetime.now(datetime.timezone.utc)
        to_post_alerts: Dict[int, List[discord.Embed]] = {}

        for game_alert in game_alerts:
            new_game_alerts = await self.process_game_alert(game_alert, headers)
            self.init = True

            if new_game_alerts:
                new_streams, alerts = new_game_alerts
                log.debug(
                    f"New streams for game {game_alert['game'].title()}: {', '.join(stream.title for stream in new_streams)}"
                )

                for stream in new_streams:
                    embed = stream.make_embed()

                    for alert in alerts:
                        to_post_alerts.setdefault(alert["channel_id"], []).append(embed)

        if to_post_alerts:
            for channel_id, embeds in to_post_alerts.items():
                channel = self.bot.get_channel(channel_id)
                if channel is not None:
                    for embeds_chunk in discord.utils.as_chunks(embeds, max_size=10):
                        try:
                            await channel.send(content="Some new streams have started: ", embeds=embeds_chunk)  # type: ignore # Will always be discord.TextChannel
                        # except discord.HTTPException:
                        #     pass
                        except Exception as error:
                            log.error(error)

    @check_streams.before_loop
    async def check_streams_before_loop(self):
        await self.bot.wait_until_ready()

    @check_streams.error
    async def check_streams_error(self, error: BaseException) -> None:
        log.error("An error got raised while annoucing new streams: ", exc_info=error)

    async def fetch_game(self, game_name: str, *, headers: dict) -> Game:
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

                game = Game(games_data[0], headers=headers)
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

    @gamestreams_twitch.command(name="search", cooldown_after_parsing=True)
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

        headers = await self.fetch_game_headers()
        if headers is None:
            await ctx.send(
                "The Twitch Client ID is not set. Please read `;streamset twitchtoken`."
            )
            return

        try:
            game = await self.fetch_game(game_name, headers=headers)
        except Exception as error:
            await ctx.send(str(error))
            return

        async with ctx.typing():
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

    @gamestreams_twitch.command(name="alert", cooldown_after_parsing=True)
    @commands.guild_only()
    @commands.has_permissions(manage_guild=True)
    @commands.cooldown(rate=1, per=10, type=commands.BucketType.member)
    async def gamestreams_twitch_alert(
        self,
        ctx: commands.GuildContext,
        channel: Optional[discord.TextChannel] = None,
        *,
        game_name: str,
    ) -> None:
        """Announce streams for a specific game."""
        if self.streams_cog is None:
            await ctx.send(
                f"Streams cog is currently not loaded. {' You can load the cog using `[p]load streams`' if await self.bot.is_owner(ctx.author) else ''}"
            )
            return

        headers = await self.fetch_game_headers()
        if headers is None:
            await ctx.send(
                "The Twitch Client ID is not set. Please read `;streamset twitchtoken`."
            )
            return

        if channel is None:
            if not isinstance(ctx.channel, discord.TextChannel):
                await ctx.send("Announcements channel must be a text channel.")
                return
            channel = ctx.channel

        try:
            game = await self.fetch_game(game_name, headers=headers)
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

    @gamestreams_twitch.command(name="alerts", cooldown_after_parsing=True)
    @commands.guild_only()
    @commands.is_owner()
    @commands.cooldown(rate=1, per=5, type=commands.BucketType.member)
    async def gamestreams_twitch_alerts(
        self,
        ctx: commands.GuildContext,
    ) -> None:
        """Check all the streams that get announced."""

        alerts = await self.config.alerts()

        embeds: List[discord.Embed] = []

        for i, alert in enumerate(alerts):
            game_name = alert["game"]
            game_alerts = alert["alerts"]

            description = ""

            for j, game_alert in enumerate(game_alerts):
                guild = ctx.bot.get_guild(game_alert["guild_id"])
                channel = guild.get_channel(game_alert["channel_id"]) if guild else None

                description += f"{j+1}. {channel.mention if channel else 'Channel Not Found'} - {guild.name if guild else 'Guild Not Found'}\n"

            embed = discord.Embed(
                title=game_name.title(),
                description=description,
                colour=discord.Colour.random(),
            )

            embed.set_footer(text=f"Page {i + 1}/{len(alerts)}")

            if description:
                embeds.append(embed)

        if embeds:
            pages = SimpleMenu(embeds, disable_after_timeout=True)  # type: ignore
            await pages.start(ctx)
        else:
            await ctx.send("No saved game alerts.")
