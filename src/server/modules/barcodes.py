"""
Handles barcodes.

Authored by Lohith Tanuku.
"""

from pyzbar import pyzbar
from pyzbar.pyzbar import ZBarSymbol
from typing import Optional
from PIL import Image
import io


def read_barcodes(raw_image: bytes) -> Optional[int]:
    """
    Reads a barcode from the supplied image. Returns the first
    EAN-13 barcode found, or `None` if no barcodes were found.
    """
    # Create an Image object from the input bytes
    image = Image.open(io.BytesIO(raw_image))

    # Convert the Image object to grayscale
    image = image.convert("L")

    # Find the barcodes in the image and decode each of the barcodes
    barcodes = pyzbar.decode(image, symbols=[ZBarSymbol.EAN13])

    # Return None if pyzbar doesn't find any barcodes
    if not barcodes:
        return None

    # Converts barcode data from a bytes object to an integer
    return int(barcodes[0])
