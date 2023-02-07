"""
This module scrapes data from FairPrice's internal API.
"""

import asyncio
import aiohttp
from modules.database import DatabaseClient
import json
import requests


db = DatabaseClient("src/client/static", "server-store")


def get_fairprice_slugs(fairprice_categories):
    """
    Gets the slugs from fairpricecategories.json to be used in the URL.
    """
    category_slugs = []
    for category in fairprice_categories:
        for sub_cat in category["menu"]:
            url = sub_cat["url"].split("/")
            category_slugs.append(url[-1])
    return category_slugs


async def extract_product(session: aiohttp.ClientSession, product: dict, top_level_cat):
    """
    Given a raw product dictionary supplied by the FairPrice API,
    extracts the necessary information and writes it to the database.
    """

    # Get product name
    name = product["name"]
    barcodes = []
    image = b""

    # Get product barcode
    try:
        barcodes = [int(bar) for bar in product["barcodes"]]
    except TypeError:
        print(product["name"], "no barcode")

    # Get product image
    try:
        image_url = product["images"][0]
        async with session.get(image_url) as res:
            image = await res.read()
    except:
        print(product["name"], "no image")

    # Adds product to database
    try:
        product_id = db.create_default_product(name, top_level_cat, barcodes, image)
    except:
        print("cannot add product")


async def scrape_page(session: aiohttp.ClientSession, category: str, page: int) -> int:

    """
    Scrapes data from one page of the API and writes it to the database.
    Returns the total number of pages in the specified category.
    """
    # generates URL for each category and page
    endpoint = api_url(category, page)

    # Get the data from the API
    async with session.get(endpoint) as res:
        body = await res.json()

    # Gets current page to show progress
    curr_page = 0
    try:
        curr_page = body["data"]["pagination"]["page"]
    except:
        print("curr_page", category, "/", page)

    # Get total pages in the category
    total_pages = 0
    try:
        total_pages = body["data"]["pagination"]["total_pages"]
    except:
        print("total_page", category, "/", page)

    # Print current progress
    print(f"Scraped page {curr_page} / {total_pages} of category {category}")

    # Gets product information from the response
    tasks = []
    try:
        for p in body["data"]["product"]:
            tasks.append(extract_product(session, p, category))
    except KeyError:
        print("no product", category, "/", page)
    await asyncio.gather(*tasks)

    # return total number of pages
    return total_pages


async def scrape_category(session: aiohttp.ClientSession, category: str):
    """Scrapes data from one category of the API and writes it to the database."""

    total_pages = await scrape_page(session, category, 1)

    # Scrape all the other pages in parallel
    tasks = [scrape_page(session, category, i) for i in range(total_pages)]
    await asyncio.gather(*tasks)


async def scrape(session: aiohttp.ClientSession):
    """Scrapes all the products from the FairPrice API and writes the scraped data to the database."""
    tasks = [scrape_category(session, cat) for cat in deepest_categories]
    await asyncio.gather(*tasks)


def api_url(product_category: str, page_number=1) -> str:
    """Returns the URL of the FairPrice API endpoint."""
    return (
        "https://website-api.omni.fairprice.com.sg/api/product/v2"
        + f"?pageType=category&url={product_category}&page={page_number}"
    )


async def main():
    """
    Runs the scraper
    """
    # Prevents aiohttp from timing out
    session_timout = aiohttp.ClientTimeout(total=None)

    async with aiohttp.ClientSession(timeout=session_timout) as session:
        await scrape(session)


# Read FairPrice categories
with open("fairprice_categories.json") as cats:
    fairprice_categories = json.load(cats)

# List of all the slugs for URL
deepest_categories = get_fairprice_slugs(fairprice_categories)

asyncio.run(main())
