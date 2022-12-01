"""
This module simulates a headless (no GUI) client, for testing purposes.
"""

import asyncio
from utils import net


def handle_login(event: net.AuthenticationEvent):
    print(event)


networker = net.Networker("http://0.0.0.0:8080")
networker.on_login = handle_login
networker.request_login("john@gmail.com", "correct horse battery staple")

asyncio.run(networker.run())