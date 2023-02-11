"""
This module scrapes data from FairPrice's internal API.

Authored by Lohith Tanuku
"""

import asyncio
import aiohttp
from modules.database import DatabaseClient
import json


class Scraper:
    def __init__(
        self,
        categories: dict[str, str],
        db,
    ):
        # Maps category slugs to category names
        self.categories: dict[str, str] = categories
        # sets the object attribute for db
        self.db = db

    async def scrape(
        self,
        session: aiohttp.ClientSession,
    ):
        """Scrapes all the products from the FairPrice API and writes the scraped data to the database."""
        tasks = [self.scrape_category(session, cat) for cat in self.categories.keys()]
        await asyncio.gather(*tasks)

    async def scrape_category(
        self,
        session: aiohttp.ClientSession,
        category: str,
    ):
        """Scrapes data from one category of the API and writes it to the database."""

        total_pages = await self.scrape_page(session, category, 1)

        # Scrape all the other pages in parallel
        tasks = [self.scrape_page(session, category, i) for i in range(total_pages)]
        await asyncio.gather(*tasks)

    async def scrape_page(
        self,
        session: aiohttp.ClientSession,
        category_slug: str,
        page: int,
    ) -> int:

        """
        Scrapes data from one page of the API and writes it to the database.
        Returns the total number of pages in the specified category.
        """
        # generates URL for each category and page
        endpoint = self.api_url(category_slug, page)

        # Get the data from the API
        async with session.get(endpoint) as res:
            body = await res.json()

        # Gets current page to show progress
        curr_page = 0
        curr_page = body["data"]["pagination"]["page"]
        """
        try:
            curr_page = body["data"]["pagination"]["page"]
        except:
            print("curr_page", category_slug, "/", page)"""

        # Get total pages in the category
        total_pages = 0
        total_pages = body["data"]["pagination"]["total_pages"]
        """
        try:
            total_pages = body["data"]["pagination"]["total_pages"]
        except:
            print("total_page", category_slug, "/", page)
        """

        # Print current progress
        print(f"Scraped page {curr_page} / {total_pages} of category {category_slug}")

        # Gets product information from the response
        tasks = []
        try:
            for p in body["data"]["product"]:
                tasks.append(self.extract_product(session, p, category_slug))
        except KeyError:
            print("no product", category_slug, "/", page)
        await asyncio.gather(*tasks)

        return total_pages

    async def extract_product(
        self,
        session: aiohttp.ClientSession,
        product: dict,
        category_slug,
    ):
        """
        Given a raw product dictionary supplied by the FairPrice API,
        extracts the necessary information and writes it to the database.
        """

        # Get product name
        name = product["name"]
        barcodes = []
        image = b""

        # Get product category
        category = self.categories[category_slug]

        # Get product barcode
        if product["barcodes"] is None:
            barcodes = []
        else:
            barcodes = [int(bar) for bar in product["barcodes"]]

        # Get product image
        if product["images"] is None:
            image = None
        else:
            image_url = product["images"][0]
            async with session.get(image_url) as res:
                image = await res.read()

        # Adds product to database
        product_id = self.db.create_default_product(name, category, barcodes, image)

    def api_url(
        self,
        product_category: str,
        page_number=1,
    ) -> str:
        """Returns the URL of the FairPrice API endpoint."""
        return (
            "https://website-api.omni.fairprice.com.sg/api/product/v2"
            + f"?pageType=category&url={product_category}&page={page_number}"
        )


async def main():
    """
    Runs the scraper
    """
    # Read FairPrice categories
    with open("fairprice_categories.json") as cats:
        fairprice_categories = json.load(cats)

    # Gets the slugs from fairpricecategories.json to be used in the URL and the Category names. Then, puts them into a dict
    categories = {}
    for cat in fairprice_categories:
        for sub_cat in cat["menu"]:
            slug = sub_cat["url"].split("/")[-1]
            category = sub_cat["name"]
            categories[slug] = category

    # Prevents aiohttp from timing out
    session_timout = aiohttp.ClientTimeout(total=None)
    db = DatabaseClient("src/client/static", "server-store")
    scraper = Scraper(categories, db)
    async with aiohttp.ClientSession(timeout=session_timout) as session:
        await scraper.scrape(session)


asyncio.run(main())
