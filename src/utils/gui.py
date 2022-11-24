"""
This module contains the GUI that runs on the client.
"""

import pyglet
import cv2
from PIL import Image
from asyncio import sleep
from utils.networker import Networker


async def main(net: Networker):
    """
    Entry point of the GUI application.
    """
    await sleep(1)
