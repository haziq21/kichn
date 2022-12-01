"""
This module handles communication with the web server from the client.

Authored by Haziq Hairil.
"""

import asyncio
import aiohttp
import websockets
from typing import Callable
from collections.abc import Coroutine
from dataclasses import dataclass


@dataclass
class AuthenticationEvent:
    """
    Represents a login or signup event. `session_token`
    will be an empty string if `successful` is `False`.
    """

    successful: bool
    session_token: str


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
        self._queued_reqs: list[Callable[[aiohttp.ClientSession], Coroutine]] = []

        #### NETWORK EVENT HANDLERS ####

        empty_fn = lambda _: None

        self.on_login: Callable[[AuthenticationEvent], None] = empty_fn
        """Runs when a login request receives a response."""

        self.on_signup: Callable[[AuthenticationEvent], None] = empty_fn
        """Runs when a signup request receives a response."""

    async def run(self):
        """
        Continuously sends scheduled requests and messages, as
        well as receives responses and messages from the server.
        """
        # Run the HTTP and WebSocket tasks concurrently
        await asyncio.gather(
            self._run_http(), self._run_ws_sender(), self._run_ws_receiver()
        )

    async def _run_http(self):
        """
        Continuously sends scheduled HTTP requests and receives responses.
        """
        async with aiohttp.ClientSession(self._server_url) as session:
            # Continuously send the queued requests
            while True:
                if len(self._queued_reqs) == 0:
                    # Allow other asyncio tasks to run if there are no queued requests
                    await asyncio.sleep(0)
                    continue

                # Run the least recently queued request
                await self._queued_reqs.pop(0)(session)

    async def _run_ws_sender(self):
        """
        Continuously sends scheduled WebSocket messages.
        """

    async def _run_ws_receiver(self):
        """
        Continuously receives WebSocket messages.
        """

    def request_login(self, email: str, password: str):
        """
        Schedules a login request to be sent. `self.on_login()`
        will be called once the response is received.
        """
        req_body = {"email": email, "password": password}

        async def req(session: aiohttp.ClientSession):
            # Make the POST request to /login
            async with session.post("/login", json=req_body) as res:
                if res.status == 200:
                    # 200 OK - the login was successful
                    session_token = (await res.json())["sessionToken"]
                    self.on_login(AuthenticationEvent(True, session_token))
                elif res.status == 401:
                    # 401 Unauthorized - the login was unsuccessful
                    self.on_login(AuthenticationEvent(False, ""))
                else:
                    # Something went wrong...
                    raise Exception(f"Unexpected {res.status} response code")

        self._queued_reqs.append(req)

    def request_signup(self, name: str, email: str, password: str):
        """
        Schedules a signup request to be sent. `self.on_signup()`
        will be called once the response is received.
        """
        req_body = {"name": name, "email": email, "password": password}

        async def req(session: aiohttp.ClientSession):
            # Make the POST request to /signup
            async with session.post("/signup", json=req_body) as res:
                if res.status == 200:
                    # 200 OK - the signup was successful
                    session_token = (await res.json())["sessionToken"]
                    self.on_login(AuthenticationEvent(True, session_token))
                elif res.status == 401:
                    # 401 Unauthorized - the signup was unsuccessful
                    self.on_login(AuthenticationEvent(False, ""))
                else:
                    # Something went wrong...
                    raise Exception(f"Unexpected {res.status} response code")

        self._queued_reqs.append(req)
