"""Implements real-time sharing."""
import aiohttp
from aiohttp import web
from typing import Awaitable, Callable, Optional


class WebSocketManager:
    """Handles WebSocket communication via a pub/sub system."""

    def __init__(self):
        # Maps topics to functions that update the corresponding UI
        self._topic_based_updaters: dict[str, set[Callable[[], Awaitable[None]]]] = {}
        # Maps session tokens to functions that update
        # the UI when a WebSocket message is received
        self._message_based_updaters: dict[str, Callable[[str], Awaitable[None]]] = {}

        # Maps session tokens to functions that unregister
        # all the UI updaters associated with the session
        self._unsubscribers: dict[str, Callable[[], None]] = {}
        # Maps session tokens to their corresponding WebSocketResponse objects
        self._connections: dict[str, web.WebSocketResponse] = {}

    async def handle_connection(self, session_token: str, ws: web.WebSocketResponse):
        """
        Sends HTML updates through the WebSocket when they're
        published. Returns when the connection is closed.
        """
        # Save the WebSocket connection to allow other methods to access it
        self._connections[session_token] = ws

        # Asynchronously loop through received messages
        async for msg in ws:
            # Call the session's message-based UI updater (if it has one)
            if session_token in self._message_based_updaters:
                self._message_based_updaters[session_token](msg.data)

        if session_token in self._unsubscribers:
            self._unsubscribers.pop(session_token)()
        self._connections.pop(session_token)

    def subscribe(
        self,
        session_token: str,
        topic_renderers: dict[str, Callable[[], str]],
        receiving_renderer: Optional[Callable[[str], str]],
    ):
        """
        Subscribes the user session to the specified topics,
        using the corresponding callbacks to update the
        UI whenever an update is published to a topic.

        `topic_callbacks` maps topics to callbacks that render the updated
        HTML. If an empty string is used as a topic, the corresponding
        callback will be called whenever a WebSocket message is received.
        """
        # Unsubscribe this session from all updates it's already subscribed to
        if session_token in self._unsubscribers:
            self._unsubscribers.pop(session_token)()

        # Maps topics to functions that update the UI for the corresponding topic
        topic_ui_updaters = {}

        for topic in topic_renderers:

            async def update_topic_ui():
                """Render updated HTML and send it to the client to update their UI."""
                ws = self._connections[session_token]
                updated_html = topic_renderers[topic]()
                await ws.send_str(updated_html)

            # Subscribe the UI updater to the topic
            self._topic_based_updaters[topic].add(update_topic_ui)
            topic_ui_updaters[topic] = update_topic_ui

        async def update_message_ui(msg: str):
            """Render updated HTML and send it to the client to update their UI."""
            if receiving_renderer:
                ws = self._connections[session_token]
                rendered_msg = receiving_renderer(msg)
                await ws.send_str(rendered_msg)

        def unsubscribe():
            """Unsubscribes this session from all its newly subscribed topics."""
            # Unsubscribe each topic UI updater from their corresponding topic
            for topic in topic_ui_updaters:
                self._topic_based_updaters[topic].remove(topic_ui_updaters[topic])

            # Remove the message UI updater if it exists
            if receiving_renderer is not None:
                self._message_based_updaters.pop(session_token)

        # Register the unsubscriber
        self._unsubscribers[session_token] = unsubscribe

    async def publish_update(self, topics: list[str]):
        """
        For every user session subscribed to a topic in `topics`,
        updates their UI using the registered rendering callback.
        """
        # Call all the UI updaters that are subscribed to the specified topics
        for topic in topics:
            for update_ui in self._topic_based_updaters[topic]:
                update_ui()
