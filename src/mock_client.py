"""
This module simulates a headless (no GUI) client, for testing purposes.
"""

import asyncio
from utils import networker


def handle_login(event: networker.AuthenticationEvent):
    print(event)


net = networker.Networker("http://0.0.0.0:8080")
net.on_login = handle_login
net.request_login("john@gmail.com", "correct horse battery staple")

asyncio.run(net.run())