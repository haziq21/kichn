"""
This module contains the web server that communicates 
with the application running on the client.
"""

from aiohttp import web
from utils.database import DatabaseClient
from utils.templating import Templator

#### HELPER FUNCTIONS ####


def html_response(body: str):
    """Returns a `web.Response` with the `text/html` content type."""
    return web.Response(body=body, content_type="text/html")


def redirect_response(url: str):
    """
    Returns a `web.Response` that instructs
    HTMX to redirect to the specified URL.
    """
    # TODO: Return the response


#### LOGIN & SIGNUP ####


async def login_page(_):
    return html_response(templator.login())


async def signup_page(_):
    return html_response(templator.signup())


async def login(request: web.Request):
    """TODO: Write this docstring."""

    body = await request.post()
    email = body["email"]
    password = body["password"]

    if not db.login_is_valid(email, password):
        # Runs if the login credentials are invalid.
        return html_response(body=templator.login_failed())
    else:
        # Runs if returned otherwise [code is good to go]
        ses_create = db.create_session(email)
        # TODO: Replace this web.Response() with the redirect_response() defined above
        # (this is essentially the code that should be written in redirect_response(),
        # except that the URL should be passed in as a parameter instead of being "/".)
        res = web.Response(headers={"HX-redirect": "/"})
        res.set_cookie("session_token", ses_create)

        return res


async def signup(request: web.Request):
    """TODO: Write this docstring."""

    body = await request.post()
    username = body["username"]
    password = body["password"]
    email = body["email"]

    if not db.create_user(username, email, password):
        # Runs if the email already exists in the user database.
        return html_response(body=templator.signup_failed())

    # Runs if returned otherwise [code is good to go]
    session_token = db.create_session(email)
    res = web.Response(status=200)
    res.set_cookie("session_token", session_token)
    return res


#### MAIN PAGE ####


async def kitchens_page(request: web.Request):
    return html_response("Hello, World!")




#### MISC ####


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
        web.get("/static/{filepath}", static_asset),
        web.get("/login", login_page),
        web.post("/login", login),
        web.get("/signup", signup_page),
        web.post("/signup", signup),
        web.get("/", kitchens_page),
    ]
)

web.run_app(app)
