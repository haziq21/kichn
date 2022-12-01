"""
This module contains the GUI that runs on the client.
"""

import pygame as pg
import cv2
from PIL import Image
from pyzbar.pyzbar import decode, ZBarSymbol
from asyncio import sleep
from time import time
from utils import net


async def run(networker: net.Networker):
    """
    Entry point of the GUI application.
    """
    await sleep(1)
