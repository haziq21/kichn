"""Implements real-time sharing."""

from aiohttp import web
from typing import Callable


class WebSocketManager:
    """Handles WebSocket communication via a pub/sub system."""

    def __init__(self):
        # Maps topics to the callbacks of subscribed user sessions
        self._subscriptions: dict[str, set[Callable[[], str]]] = {}
        # Maps session tokens to functions that unsubscribe
        # the session from all of its subscribed topics
        self._unsubscribers: dict[str, Callable[[], None]] = {}

    async def handle_connection(self, session_token: str, ws: web.WebSocketResponse):
        """
        Sends HTML updates through the WebSocket when they're
        published. Returns when the connection is closed.
        """
        # TODO: Asynchronously loop through received messages
        #     TODO: When a message is received, call the session's empty topic (if it has one)

    def subscribe(
        self,
        session_token: str,
        topic_callbacks: dict[str, Callable[[], str]],
    ):
        """
        Subscribes the user session to the specified topics,
        using the corresponding callbacks to update the
        UI whenever an update is published to a topic.

        `topic_callbacks` maps topics to callbacks that render the updated
        HTML. If an empty string is used as a topic, the corresponding
        callback will be called whenever a WebSocket message is received.
        """
        # TODO: Call the unsubscriber for this session (if there is one)

        # TODO: Add the callbacks in topic_callbacks to self._subscriptions

        def unsub_callback():
            """Unsubscribes this session from all its newly subscribed topics."""
            # TODO: Remove each topic callback in topic_callbacks from self._subscriptions

        # TODO: Add unsub_callback to self._unsubscribers

    async def publish_update(self, topics: list[str]):
        """
        For every user session subscribed to a topic in `topics`,
        updates their UI using the registered rendering callback.
        """
        # TODO: Call all the callbacks of the specified topics from self._subscriptions
