"""
This module contains the web server that communicates 
with the application running on the client.
"""

from fastapi import FastAPI, WebSocket
from utils import database
