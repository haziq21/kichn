"""
This is the Kichn application that runs on the client.
"""

import asyncio
from utils import gui
from utils.networker import Networker


async def main():
    net = Networker("http://0.0.0.0:8080")

    # Run the GUI and manage the network operations concurrently
    await asyncio.gather(gui.run(net), net.run())


asyncio.run(main())
