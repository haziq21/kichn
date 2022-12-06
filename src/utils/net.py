"""
This module handles communication with the web server from the client.

Authored by Haziq Hairil.
"""

import asyncio
import aiohttp
import websockets
from collections.abc import Coroutine
from dataclasses import dataclass

# TODO: Upgrade to Python 3.10
from typing import Callable, Optional, TypeVar


#### TYPE ALIASES ####

T = TypeVar("T")
EventHandler = Callable[[T], None]
RequestorFn = Callable[[aiohttp.ClientSession], Coroutine]


#### EVENT CLASSES ####


@dataclass
class AuthenticationEvent:
    """Represents a login or signup event."""

    successful: bool


@dataclass
class ProductInfoEvent:
    """
    Represents the receiving of information about a default or custom product.
    """

    product_id: str
    name: str
    category: str
    image_url: str
    barcodes: list[int]


@dataclass
class ProductImageEvent:
    """Represents the receiving of a product image."""

    image_url: str
    image: bytes


#### NETWORKER ####


class Networker:
    """
    Handles HTTP and WebSocket communication with the web server,
    providing an abstracted interface over raw network operations.

    HTTP requests made through this class adopt a two-part model of operation:
    request scheduling and response handling. For example, to log in, the
    `request_login()` method can be called. This method simply *schedules* an
    HTTP request to be sent; it doesn't actually send the request itself. It
    is hence non-blocking. Once the HTTP response is received, it is parsed
    into (in this case) an `AuthenticationEvent` object, which is then passed
    to the `on_login()` method as an argument. This model of operation allows
    the client-side GUI code to continue running the GUI event loop while
    waiting for HTTP responses, which makes the application feel more responsive.
    """

    def __init__(self, server_url: str):
        self._server_url = server_url
        self._queued_reqs: list[RequestorFn] = []
        self._queued_msgs: list[dict] = []
        self._ws_session_token: Optional[str] = None

        #### NETWORK EVENT HANDLERS ####

        # Set the default event handlers to empty placeholder functions
        f = lambda _: None

        self.on_login: EventHandler[AuthenticationEvent] = f
        """Runs when a login request receives a response."""

        self.on_signup: EventHandler[AuthenticationEvent] = f
        """Runs when a signup request receives a response."""

        self.on_default_product_info: EventHandler[ProductInfoEvent] = f
        """
        Runs when a request for default product 
        information receives a response.
        """

        self.on_product_image: EventHandler[ProductImageEvent] = f
        """Runs when a product image request receives a response."""

    async def run(self):
        """
        Continuously sends scheduled requests and messages, as
        well as receives responses and messages from the server.
        """
        async with aiohttp.ClientSession(self._server_url) as session:
            # Run the HTTP and WebSocket tasks concurrently
            await asyncio.gather(self._run_http(session), self._run_ws(session))

    async def _run_http(self, session: aiohttp.ClientSession):
        """
        Continuously sends scheduled HTTP requests and receives responses.
        """
        # Continuously send the queued requests
        while True:
            if len(self._queued_reqs) == 0:
                # Allow other asyncio tasks to run if there are no queued requests
                await asyncio.sleep(0)
                continue

            # Run the least recently queued request
            await self._queued_reqs.pop(0)(session)

    async def _run_ws(self, session: aiohttp.ClientSession):
        """
        Continuously sends and receives WebSocket messages once
        `self._ws_session_token` is set (which happens on a
        successful login or signup).
        """
        while True:
            if self._ws_session_token is None:
                # Allow other asyncio tasks to run if a WebSocket
                # connection hasn't already been established
                await asyncio.sleep(0)
                continue

            # Connect to the WebSocket
            async with session.ws_connect("/ws/" + self._ws_session_token) as ws:
                # Run the sender and receiver tasks concurrently
                await asyncio.gather(self._run_ws_sender(ws), self._run_ws_receiver(ws))
                break  # This should never run, but just in case...

    async def _run_ws_sender(self, ws: aiohttp.ClientWebSocketResponse):
        """
        Continuously sends scheduled WebSocket messages.
        """
        # Continuously send the queued messages
        while True:
            if len(self._queued_msgs) == 0:
                # Allow other asyncio tasks to run if there are no queued messages
                await asyncio.sleep(0)
                continue

            # Send the least recently queued message
            await ws.send_json(self._queued_msgs.pop(0))

    async def _run_ws_receiver(self, ws: aiohttp.ClientWebSocketResponse):
        """
        Continuously receives WebSocket messages.
        """

    def req_login(self, email: str, password: str):
        """
        Schedules a login request to be sent. `self.on_login()` will be called
        once the response is received. A WebSocket connection to the server
        will be established automatically if the login is successful.
        """
        req_body = {"email": email, "password": password}

        async def req(session: aiohttp.ClientSession):
            # Make the POST request to /login
            async with session.post("/login", json=req_body) as res:
                if res.status == 200:
                    # 200 OK - the login was successful
                    self.on_login(AuthenticationEvent(True))
                elif res.status == 401:
                    # 401 Unauthorized - incorrect login credentials
                    self.on_login(AuthenticationEvent(False))
                else:
                    # Something went wrong...
                    # TODO: Handle more cases
                    raise Exception(f"Unexpected {res.status} response code")

        self._queued_reqs.append(req)

    def req_signup(self, name: str, email: str, password: str):
        """
        Schedules a signup request to be sent. `self.on_signup()` will be
        called once the response is received. A WebSocket connection to the
        server will be established automatically if the signup is successful.
        """
        req_body = {"name": name, "email": email, "password": password}

        async def req(session: aiohttp.ClientSession):
            # Make the POST request to /signup
            async with session.post("/signup", json=req_body) as res:
                if res.status == 200:
                    # 200 OK - the signup was successful
                    self.on_login(AuthenticationEvent(True))
                elif res.status == 409:
                    # 409 Conflict - an account with the email address already exists
                    self.on_login(AuthenticationEvent(False))
                else:
                    # Something went wrong...
                    # TODO: Handle more cases
                    raise Exception(f"Unexpected {res.status} response code")

        self._queued_reqs.append(req)

    def req_default_product_info(self, product_id: str):
        """
        Schedules a product information request to be sent. This only works
        for default products. `self.on_default_product_info()` will be called
        once the response is received.
        """

        async def req(session: aiohttp.ClientSession):
            # Make the GET request to /product/{product_id}
            async with session.get(f"/product/{product_id}") as res:
                # TODO: Handle this better
                assert res.status == 200

                # Fire the default_product_info event with
                # the data from the JSON response body
                res_body = await res.json()
                self.on_default_product_info(
                    ProductInfoEvent(
                        product_id,
                        **res_body,
                    )
                )

        self._queued_reqs.append(req)

    def req_product_image(self, image_url: str):
        """
        Schedules a product image request to be sent.
        `self.on_product_image()` will be called once the response is received.
        """

        async def req(session: aiohttp.ClientSession):
            # Make the GET request to the supplied URL
            async with session.get(image_url) as res:
                # TODO: Handle this better
                assert res.status == 200

                # Fire the on_product_image event with
                # the image data from the response body
                res_body = await res.read()
                self.on_product_image(ProductImageEvent(image_url, res_body))

        self._queued_reqs.append(req)
