"""
This module contains the web server that communicates 
with the application running on the client.

Authored by Haziq. Typed by Evan. 
"""

from aiohttp import web
from typing import Optional
from modules.database import DatabaseClient
from modules.rendering import Renderer

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


def extract_request_owner(request: web.Request) -> Optional[str]:
    """
    Returns the email address of the user who submitted the request,
    or `None` if the request's session token is missing or invalid.
    """
    if "auth_token" in request.cookies:
        return db.get_auth_token_owner(request.cookies["auth_token"])
    return None


def is_htmx_request(request: web.Request) -> bool:
    """Returns whether the request was made by HTMX."""
    return "HX-Request" in request.headers


#### LOGIN & SIGNUP ####


async def login_page(_):
    return html_response(renderer.login())


async def signup_page(_):
    return html_response(renderer.signup())


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
        return html_response(body=renderer.login_failed())
    else:
        # Runs if returned otherwise [code is good to go]
        ses_create = db.generate_auth_token(email)
        res = htmx_redirect_response("/kitchens")
        res.set_cookie("auth_token", ses_create)

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
        return html_response(body=renderer.signup_failed())

    # Run if returned otherwise [code is good to go]
    auth_token = db.generate_auth_token(email)
    res = htmx_redirect_response("/kitchens")
    res.set_cookie("auth_token", auth_token)

    return res


#### MAIN PAGE ####


async def index(request: web.Request):
    email = extract_request_owner(request)

    if email is None:
        # Redirects user to login
        raise web.HTTPFound("/login")

    # Redirects user to list of kitchens
    raise web.HTTPFound("/kitchens")


#### KITCHEN ####


async def kitchens_page(request: web.Request):
    email = extract_request_owner(request)

    if email is None:
        # Redirects user to login if no email is inputted
        raise web.HTTPFound("/login")

    # Render and return the HTML response
    page_data = db.kitchens_page_model(email)
    return html_response(renderer.kitchens_page(page_data))


async def new_kitchen(request: web.Request):
    """
    Creates a new kitchen with the `name` specified in the
    request body, then redirects to the newly created kitchen.
    """
    email = extract_request_owner(request)

    if email is None:
        raise web.HTTPUnauthorized()

    body = await request.post()
    kitchen_name = body["name"]

    # To make the type checker happy...
    assert isinstance(kitchen_name, str)

    kitchen_id = db.create_kitchen(email, kitchen_name)
    return htmx_redirect_response(f"/kitchens/{kitchen_id}/inventory")


async def kitchen_share(request: web.Request):
    return web.Response(status=200)


async def kitchen_unshare(request: web.Request):
    return web.Response(status=200)


async def kitchen_leave(request: web.Request):
    return web.Response(status=200)


async def kitchen_index(request: web.Request):
    kitchen_id_url = request.match_info["kitchen_id"]
    # Redirect any /kitchens/{kitchen_id} request to /kitchens/{kitchen_id}/inventory
    direct_url = f"/kitchens/{kitchen_id_url}/inventory"
    raise web.HTTPFound(direct_url)


async def kitchen_settings(request: web.Request):
    email = extract_request_owner(request)

    if email is None:
        raise web.HTTPUnauthorized()

    kitchen_id = request.match_info["kitchen_id"]
    check_admin = db.user_owns_kitchen(email, kitchen_id)

    if check_admin:
        page_data = db.admin_settings_page_model(email, kitchen_id)
        return html_response(renderer.admin_settings(page_data))

    page_data = db.generic_kitchen_page_model(email, kitchen_id)
    return html_response(renderer.nonadmin_settings(page_data))


#### MISC ####


async def static_asset(request: web.Request):

    # Extract filepath id from ___?
    filepath = request.match_info["filepath"]
    file = db.get_static_asset(filepath, use_cache=False)

    if file is None:
        raise web.HTTPUnauthorized()

    # Define content type
    content_types = {
        "css": "text/css",
        "js": "text/javascript",
        "svg": "image/svg+xml",
    }

    # Take filepath's content type (e.g. picture.jpg, will extract jpg)
    file_ext = filepath.split(".")[-1]
    return web.Response(body=file, content_type=content_types[file_ext])


async def product_image(request: web.Request):
    email = extract_request_owner(request)

    if email is None:
        # The user isn't signed in
        raise web.HTTPUnauthorized()

    kitchen_id = request.match_info["kitchen_id"]
    product_id = request.match_info["product_id"]
    product_img = db.get_product_image(kitchen_id, product_id)
    access = db.user_has_access_to_kitchen(email, kitchen_id)

    if not access:
        # User has no access to kitchen
        raise web.HTTPForbidden()

    if product_img is None:
        # If image does not exist
        print("Img not found")
        raise web.HTTPNotFound()

    # Returns image in jpeg form.
    return web.Response(body=product_img, content_type="image/jpeg")


#### GROCERY LIST ####


async def grocery_page(request: web.Request):
    email = extract_request_owner(request)
    kitchen_id = request.match_info["kitchen_id"]

    if email is None:
        # Redirects user to login if no email is inputted
        raise web.HTTPFound("/login")

    # Render and return the HTML response
    page_data = db.grocery_page_model(email, kitchen_id)
    return html_response(renderer.grocery_page(page_data))


async def search_grocery(request: web.Request):
    body = await request.post()
    search_query = body["query"]
    email = extract_request_owner(request)
    kitchen_id = request.match_info["kitchen_id"]

    # To make the checker happy...
    assert isinstance(email, str)
    assert isinstance(search_query, str)

    # Render and return the HTML response
    page_data = db.grocery_page_model(email, kitchen_id, search_query)
    return html_response(renderer.grocery_partial(page_data))


async def barcode_scanner_page(request: web.Request):
    email = extract_request_owner(request)

    if email is None:
        # Redirects user to login if no email is inputted
        raise web.HTTPFound("/login")

    # Extract kitchen id from URL
    kitchen_id = request.match_info["kitchen_id"]
    page_data = db.generic_kitchen_page_model(email, kitchen_id)
    return web.Response(status=200)


async def grocery_scan_post(request: web.Request):
    return web.Response(status=200)


async def grocery_product_page(request: web.Request):
    email = extract_request_owner(request)
    kitchen_id = request.match_info["kitchen_id"]
    product_id = request.match_info["product_id"]

    if email is None:
        # Redirects user to login if no email is inputted
        raise web.HTTPFound("/login")

    page_data = db.grocery_product_page_model(email, kitchen_id, product_id)
    return html_response(renderer.grocery_product_page(page_data))


async def set_product(request: web.Request):
    email = extract_request_owner(request)
    kitchen_id = request.match_info["kitchen_id"]
    product_id = request.match_info["product_id"]

    amount = int(request.query["amount"])

    # Set product amount to the product (if user changes it)
    db.set_groc_product_count(kitchen_id, product_id, amount)
    assert isinstance(email, str)
    page_data = db.grocery_product_page_model(email, kitchen_id, product_id)

    return html_response(renderer.grocery_product_amount_partial(page_data))


async def buy_grocery_product(request: web.Request):
    kitchen_id = request.match_info["kitchen_id"]
    product_id = request.match_info["product_id"]
    body = await request.post()

    # Extract amount of [item] from body dictionary.
    amount = body["amount"]

    # Extract values of expiry year, month and date from the body dictionary.
    exp_year, exp_month, exp_day = body["yyyy"], body["mm"], body["dd"]

    # Assert that expiry and amount should be strings
    # and not integers, otherwise string values will be left out
    # And also to make the checker happy...
    assert isinstance(exp_year, str)
    assert isinstance(exp_month, str)
    assert isinstance(exp_day, str)
    assert isinstance(amount, str)

    # Convert expiry and amount into integers to be processed by buy_product function
    expiry = (int(exp_year), int(exp_month), int(exp_day))
    amount = int(amount)

    # Move product from kitchen to inventory
    db.buy_product(kitchen_id, product_id, expiry, amount)

    # Redirect the user to the grocery page
    return htmx_redirect_response(f"/kitchens/{kitchen_id}/grocery")


### INVENTORY LIST ####


async def inventory_page(request: web.Request):
    email = extract_request_owner(request)

    if email is None:
        # Redirects user to login if no email is inputted
        raise web.HTTPFound("/login")

    # Extract kitchen id from URL
    kitchen_id = request.match_info["kitchen_id"]

    # Render and return the HTML response
    page_data = db.inventory_page_model(email, kitchen_id)
    return html_response(renderer.inventory_page(page_data))


async def inventory_product_page(request: web.Request):
    email = extract_request_owner(request)

    if email is None:
        # Redirects user to login if no email is inputted
        raise web.HTTPFound("/login")

    kitchen_id = request.match_info["kitchen_id"]
    product_id = request.match_info["product_id"]

    page_data = db.inventory_product_page_model(email, kitchen_id, product_id)
    return html_response(renderer.inventory_product_page(page_data))


async def inventory_use(request: web.Request):
    # POST /kitchens/k_id/inventory/p_id/use
    # POST /kitchens/k_id/inventory/p_id/use?add-to-grocery=true
    body = await request.post()
    used = body["use"]
    email = extract_request_owner(request)
    kitchen_id = request.match_info["kitchen_id"]
    product_id = request.match_info["product_id"]

    if "add-to-grocery" in request.query:
        # TODO: placeholder db stuff

        # Redirect to inventory page
        return htmx_redirect_response(f"/kitchens/{kitchen_id}/inventory")
    else:
        return web.Response(status=200)


async def inventory_search(request: web.Request):
    return web.Response(status=200)


db = DatabaseClient("src/client/static", "server-store")
renderer = Renderer("src/client/templates")

app = web.Application()
app.add_routes(
    [
        web.get("/", index),
        web.get("/static/{filepath}", static_asset),
        web.get("/login", login_page),
        web.post("/login", login),
        web.get("/signup", signup_page),
        web.post("/signup", signup),
        #### KITCHEN ####
        web.get("/kitchens", kitchens_page),
        web.post("/kitchens", new_kitchen),
        web.get("/kitchens/{kitchen_id}/settings", kitchen_settings),
        web.post("/kitchens/{kitchen_id}/settings/share", kitchen_share),
        web.post("/kitchens/{kitchen_id}/settings/leave", kitchen_leave),
        web.get("/kitchens/{kitchen_id}", kitchen_index),
        #### GROCERY ####
        web.get("/kitchens/{kitchen_id}/grocery", grocery_page),
        web.get("/kitchens/{kitchen_id}/images/{product_id}", product_image),
        web.post("/kitchens/{kitchen_id}/grocery/search", search_grocery),
        web.get("/kitchens/{kitchen_id}/grocery/scan", barcode_scanner_page),
        web.get("/kitchens/{kitchen_id}/grocery/{product_id}", grocery_product_page),
        web.post("/kitchens/{kitchen_id}/grocery/{product_id}/set", set_product),
        web.post(
            "/kitchens/{kitchen_id}/grocery/{product_id}/buy",
            buy_grocery_product,
        ),
        #### INVENTORY ####
        web.get("/kitchens/{kitchen_id}/inventory", inventory_page),
        web.get(
            "/kitchens/{kitchen_id}/inventory/{product_id}", inventory_product_page
        ),
        web.post("/kitchens/{kitchen_id}/inventory/{product_id}/use", inventory_use),
        web.post("/kitchens/{kitchen_id}/inventory/search", inventory_search),
    ]
)

web.run_app(app)
