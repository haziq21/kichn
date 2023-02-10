""""Handles barcodes."""

from pyzbar import pyzbar
from typing import Optional


def read_barcodes(image: bytes) -> Optional[int]:
    """
    Reads a barcode from the supplied image. Returns the first
    EAN-13 barcode found, or `None` if no barcodes were found.
    """
