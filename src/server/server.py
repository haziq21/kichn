"""
This module contains the web server that communicates 
with the application running on the client.

Authored by Evan. 
"""

from aiohttp import web
from datetime import datetime
from typing import Optional
from modules.database import DatabaseClient
from modules.rendering import Renderer
from modules.sharing import WebSocketManager
from modules import barcodes


#### HELPER FUNCTIONS ####


def html_response(body: str):
    """Returns a `web.Response` with the `text/html` content type."""
    return web.Response(body=body, content_type="text/html")


def htmx_redirect_response(url: str):
    """
    Returns a `web.Response` that instructs
    HTMX to redirect to the specified URL.
    """
    return web.Response(headers={"HX-Location": url})


def extract_client_email(request: web.Request) -> Optional[str]:
    """
    Returns the email address of the user who submitted the request,
    or `None` if the request's session token is missing or invalid.
    """
    if "auth_token" in request.cookies:
        return db.get_auth_token_owner(request.cookies["auth_token"])
    return None


def get_usable_session_token(request: web.Request) -> tuple[str, bool]:
    """
    Gets the session token from the request if it has one, and creates
    a new session token otherwise. Returned tuple is in the form
    (str, bool), where the str is the session token and the bool
    indicates whether the session token was taken from the request.
    """
    # Return the session token from the request headers if it's there
    if "X-Session-Token" in request.headers:
        return request.headers["X-Session-Token"], True

    # Generate a new session token otherwise
    return db.gen_session_token(), False


#### LOGIN & SIGNUP ####


async def login_page(request: web.Request):
    """Responds with the HTML of the login page."""
    session_token, request_had_session = get_usable_session_token(request)
    return html_response(
        renderer.login_page(
            session_token,
            not request_had_session,
        )
    )


async def signup_page(request: web.Request):
    """Responds with the HTML of the signup page."""
    session_token, request_had_session = get_usable_session_token(request)
    return html_response(
        renderer.signup_page(
            session_token,
            not request_had_session,
        )
    )


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
        return html_response(body=renderer.login_failed_partial())

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
        return html_response(body=renderer.signup_failed_partial())

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
    session_token, request_had_session = get_usable_session_token(request)
    page_data = db.kitchens_page_model(email)
    return html_response(
        renderer.kitchens_page(
            page_data,
            session_token,
            not request_had_session,
        )
    )


async def create_kitchen(request: web.Request):
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
    email_owner = extract_client_email(request)
    email_other_user = body["email"]
    kitchen_id = request.match_info["kitchen_id"]

    if email_owner is None:
        raise web.HTTPUnauthorized()

    assert isinstance(email_other_user, str)
    access = db.user_has_access_to_kitchen(email_owner, kitchen_id)

    if not access:
        raise web.HTTPForbidden()

    share_kitchen = db.share_kitchen(kitchen_id, email_other_user)
    page_data = db.admin_settings_page_model(email_owner, kitchen_id)

    if share_kitchen:
        return html_response(renderer.members_list_partial(page_data))

    return html_response(renderer.members_list_partial(page_data, email_other_user))


async def kitchen_leave(request: web.Request):
    email = extract_client_email(request)
    if email is None:
        raise web.HTTPUnauthorized()

    kitchen_id = request.match_info["kitchen_id"]
    db.leave_kitchen(email, kitchen_id)
    return htmx_redirect_response("/kitchens")


async def kitchen_index(request: web.Request):
    """Redirects the user to the kitchen's inventory page."""
    # Extract the kitchen ID from the URL
    email = extract_client_email(request)

    if email is None:
        raise web.HTTPUnauthorized()

    kitchen_id = request.match_info["kitchen_id"]

    access = db.user_has_access_to_kitchen(email, kitchen_id)

    if not access:
        raise web.HTTPForbidden()

    # Redirect any /kitchens/{kitchen_id} request to /kitchens/{kitchen_id}/inventory
    raise web.HTTPFound(f"/kitchens/{kitchen_id}/inventory")


async def kitchen_settings(request: web.Request):
    """Responds with the HTML of the kitchen settings page."""
    email = extract_client_email(request)

    if email is None:
        # Redirect the user to the login page if they're not already logged in
        raise web.HTTPFound("/login")

    # Extract kitchen ID from URL
    kitchen_id = request.match_info["kitchen_id"]

    access = db.user_has_access_to_kitchen(email, kitchen_id)

    if not access:
        raise web.HTTPForbidden()

    # Check if the user is an admin, because kitchen admins and
    # non-admins have different content on their kitchen settings page
    user_is_admin = db.user_owns_kitchen(email, kitchen_id)

    session_token, request_had_session = get_usable_session_token(request)

    # Check if user is an admin.
    # If so, give admin access.
    if user_is_admin:
        # Render the HTML for if the user is the kitchen admin
        page_data = db.admin_settings_page_model(email, kitchen_id)
        html = renderer.admin_settings_page(
            page_data,
            session_token,
            not request_had_session,
        )
    else:
        # Render the HTML for if the user is not the kitchen admin
        page_data = db.generic_kitchen_page_model(email, kitchen_id)
        html = renderer.nonadmin_settings_page(
            page_data,
            session_token,
            not request_had_session,
        )

    return html_response(html)


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
    """Responds with the HTML for the grocery list page."""
    email = extract_client_email(request)

    # Extract the kitchen ID from the URL
    kitchen_id = request.match_info["kitchen_id"]

    # Redirect the user to the login page if they're not logged in
    if email is None:
        raise web.HTTPFound("/login")

    # Check if the user is allowed to access this kitchen
    if not db.user_has_access_to_kitchen(email, kitchen_id):
        raise web.HTTPForbidden()

    # Get the data needed to render the page
    page_data = db.grocery_page_model(email, kitchen_id)
    session_token, request_had_session = get_usable_session_token(request)

    def render_grocery_list_partial():
        """Renders the HTML partial of the grocery list."""
        # Get the updated page data
        page_data = db.grocery_page_model(
            email,
            kitchen_id,
        )

        # Render the HTML
        return renderer.grocery_partial(page_data)

    # Allow the user to receive WebSocket updates to this page
    ws_manager.subscribe(
        session_token,
        {
            # "{kitchen_id}.grocery" is the HTML partial ID for the grocery list
            f"{kitchen_id}.grocery": render_grocery_list_partial,
        },
    )

    # Render and return the HTML response
    return html_response(
        renderer.grocery_page(
            page_data,
            session_token,
            not request_had_session,
        )
    )


async def search_grocery(request: web.Request):
    """Filters the grocery list based on a search query."""
    email = extract_client_email(request)

    # Extract the search query from the request body
    body = await request.post()
    search_query = body["query"]

    # Extract the kitchen ID from the URL
    kitchen_id = request.match_info["kitchen_id"]

    # You can't search a grocery list if you're not logged in
    if email is None:
        raise web.HTTPUnauthorized()

    # To make the checker happy...
    assert isinstance(search_query, str)

    # Get the data required to render the page
    page_data = db.grocery_page_model(email, kitchen_id, search_query)
    session_token, _ = get_usable_session_token(request)

    def render_grocery_list_partial():
        """Renders the HTML partial of the grocery list."""
        # Get the updated page data
        page_data = db.grocery_page_model(
            email,
            kitchen_id,
            search_query,
        )

        # Render the HTML
        return renderer.grocery_partial(page_data)

    # Allow the user to receive WebSocket updates to this page
    ws_manager.subscribe(
        session_token,
        {
            # "{kitchen_id}.grocery" is the HTML partial ID for the grocery list
            f"{kitchen_id}.grocery": render_grocery_list_partial,
        },
    )

    # Render and return the HTML response
    return html_response(renderer.grocery_partial(page_data))


async def barcode_scanner_page(request: web.Request):
    """Returns the HTML for the barcode scanner page."""
    email = extract_client_email(request)

    # Redirect the user to the login page if they're not logged in
    if email is None:
        raise web.HTTPFound("/login")

    # Extract the kitchen ID from the URL
    kitchen_id = request.match_info["kitchen_id"]

    # Check if the user is allowed to access this kitchen
    if not db.user_has_access_to_kitchen(email, kitchen_id):
        raise web.HTTPForbidden()

    # Get the data required to render the page
    page_data = db.generic_kitchen_page_model(email, kitchen_id)
    session_token, request_had_session = get_usable_session_token(request)

    def render_barcode_redirector(image: bytes) -> str:
        # Scan for a barcode in the image sent by the client
        barcode = barcodes.read_barcodes(image)

        # No barcode found in this image
        if barcode is None:
            return ""

        product_id = db.get_product_id_from_barcode(barcode)

        # There is no product with this barcode
        if product_id is None:
            return ""

        # Render and return the HTML
        product_page_data = db.grocery_product_page_model(
            email,
            kitchen_id,
            product_id,
        )
        return renderer.barcode_found_partial(product_page_data)

    # Trigger a redirect (over WebSocket) once the server scans the barcode
    ws_manager.subscribe(
        session_token,
        {},
        render_barcode_redirector,
    )

    # Render and return the response
    return html_response(
        renderer.barcode_scanner_page(
            page_data,
            session_token,
            not request_had_session,
        )
    )


async def grocery_product_page(request: web.Request):
    email = extract_client_email(request)

    # Extract the kitchen and product IDs from the URL
    kitchen_id = request.match_info["kitchen_id"]
    product_id = request.match_info["product_id"]

    # Redirect the user to the login page if they're not logged in
    if email is None:
        raise web.HTTPFound("/login")

    # Get the data required to render the response
    session_token, request_had_session = get_usable_session_token(request)
    page_data = db.grocery_product_page_model(email, kitchen_id, product_id)

    def render_grocery_amount_partial():
        """Renders the HTML partial of the amount widget."""
        # Get the updated page data
        page_data = db.grocery_product_page_model(
            email,
            kitchen_id,
            product_id,
        )

        # Render the updated HTML
        return renderer.grocery_product_amount_partial(page_data)

    # Allow the user to receive WebSocket updates to this page
    ws_manager.subscribe(
        session_token,
        {
            # "{kitchen_id}.grocery" is the HTML partial ID for the grocery list
            f"{kitchen_id}.grocery.{product_id}": render_grocery_amount_partial,
        },
    )

    return html_response(
        renderer.grocery_product_page(
            page_data,
            session_token,
            not request_had_session,
        )
    )


async def set_product(request: web.Request):
    """Updates the amount of the grocery product."""
    email = extract_client_email(request)

    # You can't modify the grocery list if you're not logged in
    if email is None:
        raise web.HTTPUnauthorized()

    # Extract the kitchen and product IDs from the URL
    kitchen_id = request.match_info["kitchen_id"]
    product_id = request.match_info["product_id"]

    # Get the updated amount of the product from the URL's query parameters
    amount = int(request.query["amount"])

    # Update the database with the new amount
    db.set_groc_product_count(kitchen_id, product_id, amount)

    # Update the UI on every relevant client
    await ws_manager.publish_update(
        [
            # Update the clients on this kitchen's grocery list page
            f"{kitchen_id}.grocery",
            # Update the clients on this product's page
            f"{kitchen_id}.grocery.{product_id}",
        ]
    )

    return web.Response()


async def buy_grocery_product(request: web.Request):
    # Extract kitchen and product IDs from the URL
    kitchen_id = request.match_info["kitchen_id"]
    product_id = request.match_info["product_id"]

    # Extract the purchase data from the request body
    body = await request.post()
    amount = body["amount"]
    # To make the checker happy...
    assert isinstance(amount, str)

    if "include_expiry" in body:
        # Extract expiry date from request body
        exp_year, exp_month, exp_day = body["yyyy"], body["mm"], body["dd"]
        assert isinstance(exp_year, str)
        assert isinstance(exp_month, str)
        assert isinstance(exp_day, str)
        expiry = (int(exp_year), int(exp_month), int(exp_day))
    else:
        # No expiry date was specified
        expiry = None

    # Move product from kitchen to inventory
    db.buy_product(kitchen_id, product_id, expiry, int(amount))

    # Update the UI on every relevant client
    await ws_manager.publish_update(
        [
            # Update the clients on this kitchen's grocery list page
            f"{kitchen_id}.grocery",
            # Update the clients on this product's grocery page
            f"{kitchen_id}.grocery.{product_id}",
            # Update the clients on the inventory page
            f"{kitchen_id}.inventory",
            # Update the clients on this product's inventory page
            f"{kitchen_id}.inventory.{product_id}",
        ]
    )

    # Redirect the user to the grocery page
    return htmx_redirect_response(f"/kitchens/{kitchen_id}/grocery")


### INVENTORY LIST ####


async def inventory_page(request: web.Request):
    email = extract_client_email(request)

    # Redirect the user to the login page if they're not logged in
    if email is None:
        raise web.HTTPFound("/login")

    # Extract kitchen ID from URL
    kitchen_id = request.match_info["kitchen_id"]

    # Check if the user is supposed to have access to this kitchen
    if not db.user_has_access_to_kitchen(email, kitchen_id):
        raise web.HTTPForbidden()

    session_token, request_had_session = get_usable_session_token(request)

    # Sort the inventory list by product category
    # if the URL has a "sort-by-category" parameter
    if "sort-by-category" in request.query:

        def render_inventory_list_partial() -> str:
            """Returns the updated HTML of the inventory list, sorted by category."""
            # Get the data required to render the inventory list
            page_data = db.inventory_page_model(email, kitchen_id)
            # Render the inventory list
            return renderer.inventory_partial(page_data)

        # Allow the user to receive WebSocket updates to this page
        ws_manager.subscribe(
            session_token,
            {
                # "{kitchen_id}.inventory" is the HTML partial ID for the inventory list
                f"{kitchen_id}.inventory": render_inventory_list_partial,
            },
        )

        # Render and return the response
        page_data = db.inventory_page_model(email, kitchen_id)
        return html_response(
            renderer.inventory_page(
                page_data,
                session_token,
                not request_had_session,
            )
        )

    # Sort the inventory list by expiry date
    # if the "sort-by-category" parameter isn't there
    def render_sorted_inventory_list_partial() -> str:
        """Returns the updated HTML of the inventory list, sorted by expiry date."""
        # Get the data required to render the inventory list
        page_data = db.sorted_inventory_page_model(email, kitchen_id)
        # Render the inventory list
        return renderer.sorted_inventory_partial(page_data)

    # Allow the user to receive WebSocket updates to this page
    ws_manager.subscribe(
        session_token,
        {
            # "{kitchen_id}.inventory" is the HTML partial ID for the inventory list
            f"{kitchen_id}.inventory": render_sorted_inventory_list_partial,
        },
    )

    # Render and return the response
    page_data = db.sorted_inventory_page_model(email, kitchen_id)
    return html_response(
        renderer.sorted_inventory_page(
            page_data,
            session_token,
            not request_had_session,
        )
    )


async def inventory_product_page(request: web.Request):
    """Responds with the HTML of an inventory product's page."""
    email = extract_client_email(request)

    # Redirect the user to the login page if they're not logged in
    if email is None:
        raise web.HTTPFound("/login")

    # Extract the kitchen and product IDs from the URL
    kitchen_id = request.match_info["kitchen_id"]
    product_id = request.match_info["product_id"]
    access = db.user_has_access_to_kitchen(email, kitchen_id)

    # Check if the user has access to this kitchen
    if not access:
        raise web.HTTPForbidden()

    # Render the response
    page_data = db.inventory_product_page_model(email, kitchen_id, product_id)
    session_token, request_had_session = get_usable_session_token(request)

    def render_inventory_product_partial():
        """Renders the HTML partial of the amount selector."""
        # Get the updated page data
        page_data = db.inventory_product_page_model(
            email,
            kitchen_id,
            product_id,
        )

        # Render the updated HTML
        return renderer.inventory_product_partial(page_data)

    # Allow the user to receive WebSocket updates to this page
    ws_manager.subscribe(
        session_token,
        {
            # "{kitchen_id}.grocery" is the HTML partial ID for the grocery list
            f"{kitchen_id}.inventory.{product_id}": render_inventory_product_partial,
        },
    )

    # Render and return the response
    return html_response(
        renderer.inventory_product_page(
            page_data,
            session_token,
            not request_had_session,
        )
    )


async def use_inventory_product(request: web.Request):
    email = extract_client_email(request)

    # Extract the kitchen and product IDs from the URL
    kitchen_id = request.match_info["kitchen_id"]
    product_id = request.match_info["product_id"]

    # You can't remove inventory products if you're not logged in
    if email is None:
        raise web.HTTPUnauthorized()

    # Get the data required to render the page
    page_data = db.inventory_product_page_model(email, kitchen_id, product_id)

    # Return a confirmation dialogue asking the user if
    # they want to add the product to the grocery list
    if "move-to-grocery" not in request.query:
        return html_response(renderer.inventory_product_confirmation_partial(page_data))

    body = await request.post()
    expiry_amounts = {}

    # Extract the expiry data from the request body
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

    # Update the database
    db.use_product(kitchen_id, product_id, expiry_amounts, move_to_grocery)

    # Update the UI on every relevant client
    await ws_manager.publish_update(
        [
            # Update the clients on the inventory page
            f"{kitchen_id}.inventory",
            # Update the clients on this product's inventory page
            f"{kitchen_id}.inventory.{product_id}",
        ]
    )

    if move_to_grocery:
        await ws_manager.publish_update(
            [
                # Update the clients on the grocery page
                f"{kitchen_id}.grocery",
                # Update the clients on this product's grocery page
                f"{kitchen_id}.grocery.{product_id}",
            ]
        )

    return htmx_redirect_response(f"/kitchens/{kitchen_id}/inventory")


async def inventory_search(request: web.Request):
    # TODO: Whoops not implemented
    return web.Response(status=200)


# Authored by Haziq Hairil
async def websocket(request: web.Request):
    """Handles WebSocket connections."""
    # Extract the session token from the URL
    session_token = request.match_info["session_token"]

    # Upgrade the connection from HTTP to WebSocket
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    # Let the WebSocketManager do the work
    await ws_manager.handle_connection(session_token, ws)

    return ws


db = DatabaseClient("src/client/static", "server-store")
renderer = Renderer("src/client/templates")
ws_manager = WebSocketManager()

app = web.Application()
app.add_routes(
    [
        #### REDIRECTS ####
        web.get("/", index),
        web.get("/kitchens/{kitchen_id}", kitchen_index),  #
        #### MISC ####
        web.get("/static/{filepath}", static_asset),
        web.get("/kitchens/{kitchen_id}/images/{product_id}", product_image),
        web.get("/ws/{session_token}", websocket),
        #### LOGIN & SIGNUP ####
        web.get("/login", login_page),
        web.post("/login", login),
        web.get("/signup", signup_page),
        web.post("/signup", signup),
        #### KITCHEN LIST ####
        web.get("/kitchens", kitchens_page),
        web.post("/kitchens", create_kitchen),
        #### KITCHEN SETTINGS ####
        web.get("/kitchens/{kitchen_id}/settings", kitchen_settings),  #
        web.post("/kitchens/{kitchen_id}/settings/share", kitchen_share),
        web.post("/kitchens/{kitchen_id}/settings/leave", kitchen_leave),
        #### GROCERY LIST ####
        web.get("/kitchens/{kitchen_id}/grocery", grocery_page),  #
        web.post("/kitchens/{kitchen_id}/grocery/search", search_grocery),
        web.get("/kitchens/{kitchen_id}/grocery/scan", barcode_scanner_page),  #
        #### GROCERY PRODUCT ####
        web.get("/kitchens/{kitchen_id}/grocery/{product_id}", grocery_product_page),  #
        web.post("/kitchens/{kitchen_id}/grocery/{product_id}/set", set_product),
        web.post(
            "/kitchens/{kitchen_id}/grocery/{product_id}/buy",
            buy_grocery_product,
        ),
        #### INVENTORY LIST ####
        web.get("/kitchens/{kitchen_id}/inventory", inventory_page),  #
        web.post("/kitchens/{kitchen_id}/inventory/search", inventory_search),
        #### INVENTORY PRODUCT ####
        web.get(
            "/kitchens/{kitchen_id}/inventory/{product_id}",
            inventory_product_page,
        ),
        web.post(
            "/kitchens/{kitchen_id}/inventory/{product_id}/use", use_inventory_product
        ),
    ]
)

web.run_app(app)
