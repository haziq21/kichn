"""
This module contains the web server that communicates 
with the application running on the client.
"""

from fastapi import FastAPI, WebSocket
from pydantic import BaseModel
from utils import database

app = FastAPI()


class LoginDetails(BaseModel):
    pass


class SignupDetails(LoginDetails):
    pass


@app.post("/login")
def login(login_details: LoginDetails):
    pass


@app.post("/signup")
def signup(signup_details: SignupDetails):
    pass
