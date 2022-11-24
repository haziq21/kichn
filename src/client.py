"""
This is the Kichn application that runs on the client.
"""

import asyncio
from utils import gui
from utils.networker import Networker


async def main():
    net = Networker()

    # Run the GUI and manage the network operations asynchronously
    await asyncio.gather(gui.run(net), net.run())


asyncio.run(main())
