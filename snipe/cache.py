import collections
from typing import Deque, Generic, List, NamedTuple, Optional, TypeVar, Union

import discord

T = TypeVar("T")  # Define a type variable 'T'


class EditedMessage(NamedTuple):
    before: discord.Message
    after: discord.Message


class Messages(Generic[T]):
    def __init__(self, maxsize: int):
        self.queue: Deque[T] = collections.deque(maxlen=maxsize)

    def __str__(self):
        return str(self.queue)

    def __repr__(self) -> str:
        return repr(self.queue)

    def __iter__(self):
        return iter(self.queue)

    @property
    def length(self) -> int:
        return len(self.queue)

    def add(self, value: T):
        self.queue.appendleft(value)

    def pop(self) -> T:
        return self.queue.pop()

    def get(
        self, index: int, author: Optional[Union[discord.Member, discord.User]] = None
    ) -> Optional[T]:
        raise NotImplemented

    def get_bulk(
        self, author: Optional[Union[discord.Member, discord.User]] = None
    ) -> List[T]:
        raise NotImplemented


class DeletedMessages(Messages[discord.Message]):
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


class EditedMessages(Messages[EditedMessage]):
    def get(
        self, index: int, author: Optional[Union[discord.Member, discord.User]] = None
    ) -> Optional[EditedMessage]:
        messages = list(
            filter(
                lambda edited_message: edited_message.before.author == author,
                self.queue,
            )
            if author is not None
            else self.queue
        )

        for i, message in enumerate(messages):
            if i == index:
                return message

    def get_bulk(
        self, author: Optional[Union[discord.Member, discord.User]] = None
    ) -> List[EditedMessage]:
        return list(
            filter(
                lambda edited_message: edited_message.before.author == author,
                self.queue,
            )
            if author is not None
            else self.queue
        )
