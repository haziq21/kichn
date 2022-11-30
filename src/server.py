"""
This module contains the web server that communicates 
with the application running on the client.
"""

from aiohttp import web
from utils import database


async def login(request: web.Request):
    """
    Responds with a session token if the login credentials are valid.

    The following is an example of the expected request body.

    ```json
    {
        "email": "john@gmail.com",
        "password": "correct horse battery staple"
    }
    ```

    - 400 Bad Request is returned if the request body does not include these fields.
    - 401 Unauthorized is returned if the login credentials are invalid.
    - 200 OK is returned otherwise, along with a session token.

    ```json
    {
        "sessionToken": "R7qnHymktvYDnpfb7ExB"
    }
    ```
    """
    return web.Response()


async def signup(request: web.Request):
    """
    Creates a new user account in the database and responds with a session token.

    The following is an example of the expected request body.

    ```json
    {
        "name": "John Doe",
        "email": "john@gmail.com",
        "password": "correct horse battery staple"
    }
    ```

    - 400 Bad Request is returned if the request body does not include these fields.
    - 409 Conflict is returned if the email already exists in the user database.
    - 200 OK is returned otherwise, along with a session token.

    ```json
    {
        "sessionToken": "R7qnHymktvYDnpfb7ExB"
    }
    ```
    """
    return web.Response()


app = web.Application()
app.add_routes(
    [
        web.post("/login", login),
        web.post("/signup", signup),
    ]
)

web.run_app(app)
