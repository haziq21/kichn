from aiohttp import web


class WSManager:
    """
    Handles WebSocket connections and real-time
    sharing logic with a pub/sub system.
    """

    def __init__(self):
        # Maps URLs to WS connections from users who are at the URL
        self._subs_by_page: dict[str, set[web.WebSocketResponse]] = {}
        # Maps kitchen IDs to WS connections from
        # users who are at a URL in the kitchen
        self._subs_by_kitchen: dict[str, set[web.WebSocketResponse]] = {}
        # Maps email addresses to WS connections
        # from users with the email address
        self._subs_by_email: dict[str, set[web.WebSocketResponse]] = {}

    def subscribe(self, email: str, kitchen_ids: list[str]):
        """Subscribe the specified user to the specified kitchens."""

    def unsubscribe(self, email: str, kitchen_id: str):
        """Unsubscribe the specified user from the specified kitchen."""

    async def handle_connection(self, email: str, ws: web.WebSocketResponse):
        """
        Sends HTML updates through the WebSocket when they
        are published. Returns when the connection is closed.
        """

    async def publish_to_page(self, page: str, html: str):
        """Sends the HTML to every client on the same page."""

    async def publish_to_email(self, email: str, html: str):
        """Sends the HTML to every client with the same email address."""

    async def publish_to_kitchen(self, kitchen_id: str, html: str):
        """Sends the HTML to every client with the same email address."""
