"""
This module contains the web server that communicates 
with the application running on the client.
"""

from aiohttp import web
from utils import database


async def login(request: web.Request):
    body = await request.post()
    login = body["login"]
    password = body["password"]

    """
    if "email" not in body or "password" not in body:
        return web.json_response(status=400)
        # Runs if the request body does not include these fields.
    """

    if not (database.login_is_valid(body["email"], body["password"])):
        res = web.Response(status=401)
        return res
        # Runs if the login credentials are invalid.

    else:
        ses_create = database.create_session(body["email"])
        res = web.Response(status=200)
        res.set_cookie("session_Token", ses_create)
        return res

        # Runs if returned otherwise [code is good to go]

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


async def signup(request: web.Request):
    apply = await request.post()
    login = apply["login"]
    password = apply["password"]

    """
    if "name" not in apply or "email" not in apply or "password" not in apply:
        return web.json_response(status=400)
        # Runs if the request body does not include these fields.
    """

    if not database.create_user(apply["name"], apply["email"], apply["password"]):
        res = web.Response(status=409)
        return res
        # Runs if the email already exists in the user database.

    ses_create = database.create_session(apply["email"])
    res = web.Response(status=200)
    res.set_cookie("session_token", ses_create)
    return res

    # Runs if returned otherwise [code is good to go]

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


async def kitchens_page(request: web.Request):
    pass


app = web.Application()
app.add_routes(
    [
        web.post("/login", login),
        web.post("/signup", signup),
        web.get("/login", login),
        web.post("/signup", signup),
        web.get("/kitchens", kitchens_page),
    ]
)

web.run_app(app)

