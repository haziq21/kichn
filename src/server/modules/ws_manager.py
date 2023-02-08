from aiohttp import web
from typing import Callable


class WebSocketManager:
    """
    Handles WebSocket connections and real-time
    sharing logic with a pub/sub system.
    """

    def __init__(self):
        # Maps session tokens to the WS connection used by the corresponding user
        self._subscribers: dict[str, web.WebSocketResponse] = {}
        # Maps topics to the session tokens of sessions subscribed to the topic
        self._subscriptions: dict[str, str] = {}

    def subscribe(
        self,
        session_token: str,
        topic_callbacks: dict[str, Callable[[], str]],
    ):
        """
        Subscribes the user session to the specified topics,
        using the corresponding callbacks to update the
        UI whenever an update is published to a topic.

        `topic_callbacks` maps topics to
        callbacks that render the updated HTML.
        """

    async def handle_connection(self, session_token: str, ws: web.WebSocketResponse):
        """
        Sends HTML updates through the WebSocket when they're
        published. Returns when the connection is closed.
        """

    async def publish_update(self, topics: list[str]):
        """
        For every user session subscribed to a topic in `topics`,
        updates their UI using the registered redering callback.
        """
