import collections
from typing import List, Optional, Union

import discord


class Messages:
    def __init__(self, maxsize: int):
        self.queue = collections.deque(maxlen=maxsize)

    def __str__(self):
        return str(self.queue)

    def __repr__(self) -> str:
        return repr(self.queue)

    def __iter__(self):
        return iter(self.queue)

    @property
    def length(self) -> int:
        return len(self.queue)

    def add(self, value: discord.Message):
        self.queue.appendleft(value)

    def pop(self):
        return self.queue.pop()

    def get(
        self, index: int, author: Optional[Union[discord.Member, discord.User]] = None
    ) -> Optional[discord.Message]:
        messages = list(
            filter(lambda message: message.author == author, self.queue)
            if author is not None
            else self.queue
        )

        for i, message in enumerate(messages):
            if i == index:
                return message

    def get_bulk(
        self, author: Optional[Union[discord.Member, discord.User]] = None
    ) -> List[discord.Message]:
        return list(
            filter(lambda message: message.author == author, self.queue)
            if author is not None
            else self.queue
        )
