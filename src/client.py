"""
This is the Kichn application that runs on the client.
"""

import asyncio
from utils import gui, net


async def main():
    networker = net.Networker("http://0.0.0.0:8080")

    # Run the GUI and manage the network operations concurrently
    await asyncio.gather(gui.run(networker), networker.run())


asyncio.run(main())
