"""
This module contains the web server that communicates 
with the application running on the client.

Authored by Haziq. Typed by Evan. 
"""

from aiohttp import web
from datetime import date, datetime
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


def extract_client_email(request: web.Request) -> Optional[str]:
    """
    Returns the email address of the user who submitted the request,
    or `None` if the request's session token is missing or invalid.
    """
    if "auth_token" in request.cookies:
        return db.get_auth_token_owner(request.cookies["auth_token"])
    return None


#### LOGIN & SIGNUP ####


async def login_page(_):
    """Responds with the HTML of the login page."""
    return html_response(renderer.login())


async def signup_page(_):
    """Responds with the HTML of the signup page."""
    return html_response(renderer.signup())


async def login(request: web.Request):
    """Logs a user into their account."""
    # Extract user data from the request body
    body = await request.post()
    email = body["email"]
    password = body["password"]

    # To make the type checker happy...
    assert isinstance(email, str)
    assert isinstance(password, str)

    if not db.login_is_valid(email, password):
        # Display an error message if the login credential's are invalid
        return html_response(body=renderer.login_failed())

    # Redirect the user to the kitchen list page
    res = htmx_redirect_response("/kitchens")

    # Set an authentication token cookie
    auth_token = db.generate_auth_token(email)
    res.set_cookie("auth_token", auth_token)

    return res


async def signup(request: web.Request):
    """Creates a user account."""
    # Extract user data from the request body
    body = await request.post()
    email = body["email"]
    username = body["username"]
    password = body["password"]

    # To make the type checker happy...
    assert isinstance(username, str)
    assert isinstance(email, str)
    assert isinstance(password, str)

    if not db.create_user(username, email, password):
        # Display an error message if an account
        # with the supplied email already exists
        return html_response(body=renderer.signup_failed())

    # Redirect the user to the kitchen list page
    res = htmx_redirect_response("/kitchens")

    # Set an authentication token cookie
    auth_token = db.generate_auth_token(email)
    res.set_cookie("auth_token", auth_token)

    return res


#### MAIN PAGE ####


async def index(request: web.Request):
    """
    Redirect the user to the appropriate page
    based on whether they're logged in or not.
    """
    email = extract_client_email(request)

    if email is None:
        # Redirect user to login
        raise web.HTTPFound("/login")

    # Redirect user to the kitchen list page
    raise web.HTTPFound("/kitchens")


#### KITCHEN ####


async def kitchens_page(request: web.Request):
    """Responds with the HTML of the kitchen list page."""
    email = extract_client_email(request)

    if email is None:
        # Redirect the user to the login page if they're not already logged in
        raise web.HTTPFound("/login")

    # Render and return the HTML response
    page_data = db.kitchens_page_model(email)
    return html_response(renderer.kitchens_page(page_data))


async def new_kitchen(request: web.Request):
    """Creates a new kitchen and redirects to it."""
    email = extract_client_email(request)

    # You can't create a kitchen if you're not logged in
    if email is None:
        raise web.HTTPUnauthorized()

    # Extract the kitchen name from the request body
    body = await request.post()
    kitchen_name = body["name"]

    # To make the type checker happy...
    assert isinstance(kitchen_name, str)

    # Render and return the HTML response
    kitchen_id = db.create_kitchen(email, kitchen_name)
    return htmx_redirect_response(f"/kitchens/{kitchen_id}/inventory")


async def kitchen_share(request: web.Request):
    body = await request.post()
    email = body["email"]
    kitchen_id = request.match_info["kitchen_id"]

    assert isinstance(email, str)
    page_data = db.admin_settings_page_model(email, kitchen_id)

    assert isinstance(email, str)
    share_kitchen = db.share_kitchen(kitchen_id, email)

    if share_kitchen:
        return html_response(renderer.members_list_partial(page_data))

    return html_response(renderer.members_list_partial(page_data, email))


async def kitchen_leave(request: web.Request):
    return web.Response(status=200)


async def kitchen_index(request: web.Request):
    kitchen_id_url = request.match_info["kitchen_id"]
    # Redirect any /kitchens/{kitchen_id} request to /kitchens/{kitchen_id}/inventory
    direct_url = f"/kitchens/{kitchen_id_url}/inventory"
    raise web.HTTPFound(direct_url)


async def kitchen_settings(request: web.Request):
    email = extract_client_email(request)

    if email is None:
        raise web.HTTPUnauthorized()

    kitchen_id = request.match_info["kitchen_id"]
    check_admin = db.user_owns_kitchen(email, kitchen_id)

    if check_admin:
        page_data = db.admin_settings_page_model(email, kitchen_id)
        return html_response(renderer.admin_settings_page(page_data))

    page_data = db.generic_kitchen_page_model(email, kitchen_id)
    return html_response(renderer.nonadmin_settings_page(page_data))


#### MISC ####


async def static_asset(request: web.Request):

    # Extract filepath id from ?
    filepath = request.match_info["filepath"]
    file = db.get_static_asset(filepath, use_cache=False)

    if file is None:
        raise web.HTTPNotFound()

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
    email = extract_client_email(request)

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
        raise web.HTTPNotFound()

    # Return the JPEG
    return web.Response(body=product_img, content_type="image/jpeg")


#### GROCERY LIST ####


async def grocery_page(request: web.Request):
    email = extract_client_email(request)
    kitchen_id = request.match_info["kitchen_id"]

    if email is None:
        # Redirects user to login if no email is inputted
        raise web.HTTPFound("/login")

    # Render and return the HTML response
    page_data = db.grocery_page_model(email, kitchen_id)
    return html_response(renderer.grocery_page(page_data))


async def search_grocery(request: web.Request):
    """Filters the grocery list based on a search query."""
    # Extract the search query from the request body
    body = await request.post()
    search_query = body["query"]

    email = extract_client_email(request)
    kitchen_id = request.match_info["kitchen_id"]

    # You can't search a grocery list if you're not logged in
    if email is None:
        raise web.HTTPUnauthorized()

    # To make the checker happy...
    assert isinstance(search_query, str)

    # Render and return the HTML response
    page_data = db.grocery_page_model(email, kitchen_id, search_query)
    return html_response(renderer.grocery_partial(page_data))


async def barcode_scanner_page(request: web.Request):
    email = extract_client_email(request)

    if email is None:
        # Redirects user to login if no email is inputted
        raise web.HTTPFound("/login")

    # Extract kitchen id from URL
    kitchen_id = request.match_info["kitchen_id"]
    page_data = db.generic_kitchen_page_model(email, kitchen_id)
    return html_response(renderer.barcode_scanner_page(page_data))


async def grocery_product_page(request: web.Request):
    email = extract_client_email(request)
    kitchen_id = request.match_info["kitchen_id"]
    product_id = request.match_info["product_id"]

    if email is None:
        # Redirects user to login if no email is inputted
        raise web.HTTPFound("/login")

    page_data = db.grocery_product_page_model(email, kitchen_id, product_id)
    return html_response(renderer.grocery_product_page(page_data))


async def set_product(request: web.Request):
    email = extract_client_email(request)
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

    if "include_expiry" in body:
        exp_year, exp_month, exp_day = body["yyyy"], body["mm"], body["dd"]
        assert isinstance(exp_year, str)
        assert isinstance(exp_month, str)
        assert isinstance(exp_day, str)
        expiry = (int(exp_year), int(exp_month), int(exp_day))

    else:
        expiry = None

    # Assert that expiry and amount should be strings
    # and not integers, otherwise string values will be left out
    # And also to make the checker happy...

    assert isinstance(amount, str)

    # Convert amount into integer to be processed by buy_product function
    amount = int(amount)

    # Move product from kitchen to inventory
    db.buy_product(kitchen_id, product_id, expiry, amount)

    # Redirect the user to the grocery page
    return htmx_redirect_response(f"/kitchens/{kitchen_id}/grocery")


### INVENTORY LIST ####


async def inventory_page(request: web.Request):
    email = extract_client_email(request)

    if email is None:
        # Redirects user to login if no email is inputted
        raise web.HTTPFound("/login")

    # Extract kitchen id from URL
    kitchen_id = request.match_info["kitchen_id"]
    product_id = request.match_info["product_id"]

    # Render and return the HTML response
    page_data = db.inventory_page_model(email, kitchen_id)

    if "sort-by-category" in request.query:
        return html_response(renderer.inventory_page(page_data))

    page_data = db.sorted_inventory_page_model(email, kitchen_id, product_id)
    return html_response(renderer.sorted_inventory_page(page_data))


async def inventory_product_page(request: web.Request):
    email = extract_client_email(request)

    if email is None:
        # Redirects user to login if no email is inputted
        raise web.HTTPFound("/login")

    kitchen_id = request.match_info["kitchen_id"]
    product_id = request.match_info["product_id"]

    page_data = db.inventory_product_page_model(email, kitchen_id, product_id)
    return html_response(renderer.inventory_product_page(page_data))


async def use_inventory_product(request: web.Request):
    email = extract_client_email(request)
    kitchen_id = request.match_info["kitchen_id"]
    product_id = request.match_info["product_id"]

    if email is None:
        raise web.HTTPUnauthorized()

    page_data = db.inventory_product_page_model(email, kitchen_id, product_id)

    if "move-to-grocery" not in request.query:
        return html_response(renderer.inventory_product_confirmation_partial(page_data))

    body = await request.post()
    expiry_amounts = {}

    for expiry_str in body:
        if expiry_str == "non_expirables":
            expiry = None

        else:
            expiry = datetime.strptime(expiry_str, "%Y-%m-%d").date()

        amount_str = body[expiry_str]
        assert isinstance(amount_str, str)

        amount = int(amount_str)
        expiry_amounts[expiry] = amount

    move_to_grocery = request.query["move-to-grocery"] == "true"
    db.use_product(kitchen_id, product_id, expiry_amounts, move_to_grocery)

    return htmx_redirect_response(f"/kitchens/{kitchen_id}/inventory")


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
        web.post(
            "/kitchens/{kitchen_id}/inventory/{product_id}/use", use_inventory_product
        ),
        web.post("/kitchens/{kitchen_id}/inventory/search", inventory_search),
    ]
)

web.run_app(app)
