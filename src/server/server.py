"""
This module contains the web server that communicates 
with the application running on the client.
"""

from aiohttp import web
from typing import Optional
from utils.database import DatabaseClient
from utils.templating import Templator

#### HELPER FUNCTIONS ####


def html_response(body: str):
    """Returns a `web.Response` with the `text/html` content type."""
    return web.Response(body=body, content_type="text/html")


def htmx_redirect_response(url: str):
    """
    Returns a `web.Response` that instructs
    HTMX to redirect to the specified URL.
    """
    return web.Response(headers={"HX-Redirect": url})


def redirect_response(url: str):
    """
    Raises web.HTTPFound exception
    """
    raise web.HTTPFound(url)


def extract_request_owner(request: web.Request) -> Optional[str]:
    """
    Returns the email address of the user who submitted the request,
    or `None` if the request's session token is missing or invalid.
    """
    if "session_token" in request.cookies:
        return db.get_session_owner(request.cookies["session_token"])
    return None


def is_htmx_request(request: web.Request) -> bool:
    """Returns whether the request was made by HTMX."""
    return "HX-Request" in request.headers


#### LOGIN & SIGNUP ####


async def login_page(_):
    return html_response(templator.login())


async def signup_page(_):
    return html_response(templator.signup())


async def login(request: web.Request):
    """Starts a user session if the login credentials are valid."""
    body = await request.post()
    email = body["email"]
    password = body["password"]

    # To make the type checker happy...
    assert isinstance(email, str)
    assert isinstance(password, str)

    if not db.login_is_valid(email, password):
        # Runs if the login credentials are invalid.
        return html_response(body=templator.login_failed())
    else:
        # Runs if returned otherwise [code is good to go]
        ses_create = db.create_session(email)
        res = htmx_redirect_response("/kitchens")
        res.set_cookie("session_token", ses_create)

        return res


async def signup(request: web.Request):
    """Creates the user account and starts a user session."""
    body = await request.post()
    username = body["username"]
    password = body["password"]
    email = body["email"]

    # To make the type checker happy...
    assert isinstance(username, str)
    assert isinstance(email, str)
    assert isinstance(password, str)

    if not db.create_user(username, email, password):
        # Runs if the email already exists in the user database.
        return html_response(body=templator.signup_failed())

    # Runs if returned otherwise [code is good to go]
    session_token = db.create_session(email)
    res = htmx_redirect_response("/kitchens")
    res.set_cookie("session_token", session_token)

    return res


#### MAIN PAGE ####


async def index(request: web.Request):
    email = extract_request_owner(request)

    if email is None:
        redirect_response("/login")

    redirect_response("/kitchens")


async def kitchens_page(request: web.Request):

    email = extract_request_owner(request)

    if email is None:
        redirect_response("/login")

    kitchens = db.get_kitchens(email)
    info_user = db.get_user(email)
    return html_response(templator.kitchens(kitchens, info_user))


async def new_kitchen(request: web.Request):
    """
    Creates a new kitchen with the `name` specified in the
    request body, then redirects to the newly created kitchen.
    """
    user_email = extract_request_owner(request)

    if user_email is None:
        return web.Response(status=401)

    body = await request.post()
    kitchen_name = body["name"]

    # To make the type checker happy...
    assert isinstance(kitchen_name, str)

    kitchen_id = db.create_kitchen(user_email, kitchen_name)
    return htmx_redirect_response(f"/kitchens/{kitchen_id}/inventory")


#### KITCHEN INVENTORY ####


async def kitchen_inventory_page(request: web.Request):

    user_email = extract_request_owner(request)

    if user_email is None:
        return redirect_response("/login")

    kitchen_id = request.match_info["kitchen_id"]
    inv_list = db.get_inventory_list(kitchen_id)
    user_acc = db.get_user(user_email)

    return html_response(templator.inventory(inv_list, user_acc))


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
        web.get("/", index),
        web.get("/static/{filepath}", static_asset),
        web.get("/login", login_page),
        web.post("/login", login),
        web.get("/signup", signup_page),
        web.post("/signup", signup),
        web.get("/kitchens", kitchens_page),
        web.post("/kitchens", new_kitchen),
        web.get("/kitchens/{kitchen_id}/inventory", kitchen_inventory_page),
    ]
)

web.run_app(app)
