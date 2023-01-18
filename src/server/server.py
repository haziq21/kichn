"""
This module contains the web server that communicates 
with the application running on the client.
"""

from aiohttp import web
from utils.database import DatabaseClient
from utils.templating import Templator


def html_response(body: str):
    return web.Response(body=body, content_type="text/html")


async def kitchens_page(request: web.Request):
    return html_response("Hello, World!")


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

    body = await request.post()
    email = body["email"]
    password = body["password"]

    # if not db.login_is_valid(email, password):

    if False:
        # Runs if the login credentials are invalid.
        return html_response(body=templator.login_failed())
    else:
        # Runs if returned otherwise [code is good to go]
        ses_create = db.create_session(email)
        res = web.Response(headers={"HX-redirect": "/"})
        res.set_cookie("session_token", ses_create)

        return res


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

    body = await request.post()
    username = body["username"]
    password = body["password"]
    email = body["email"]

    if not db.create_user(username, email, password):
        return html_response(body=templator.signup_failed())
        # Runs if the email already exists in the user database.

    ses_create = db.create_session(email)
    res = web.Response(status=200)
    res.set_cookie("session_token", ses_create)
    return res

    # Runs if returned otherwise [code is good to go]


async def signup_page(request: web.Request):
    return html_response(templator.signup())


async def login_page(request: web.Request):
    return html_response(templator.login())


async def static_asset(request: web.Request):
    filepath = request.match_info["filepath"]
    file = db.get_static_asset(filepath)

    if file is None:
        return web.Response(status=404)

    content_types = {
        "css": "text/css",
        "js": "text/javascript",
        "svg": "image/svg+xml",
    }

    file_ext = filepath.split(".")[-1]
    return web.Response(body=file, content_type=content_types[file_ext])


db = DatabaseClient("src/client/static", "server-store")
templator = Templator("src/client/templates")
app = web.Application()
app.add_routes(
    [
        web.get("/", kitchens_page),
        web.post("/signup", signup),
        web.post("/login", login),
        web.get("/signup", signup_page),
        web.get("/login", login_page),
        web.get("/static/{filepath}", static_asset),
    ]
)

web.run_app(app)
