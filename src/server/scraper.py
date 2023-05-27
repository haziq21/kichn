"""
This module scrapes data from FairPrice's internal API.

Authored by Lohith Tanuku. Co-authored by Haziq Hairil.
"""

import asyncio
import aiohttp
import bs4
import json
from modules.database import DatabaseClient


class Scraper:
    def __init__(self, db: DatabaseClient, session: aiohttp.ClientSession):
        self.db: DatabaseClient = db
        self.session: aiohttp.ClientSession = session

        # Maps category slugs to category names
        self.categories: dict[str, str] = {}

        self.products_discovered: int = 0
        self.products_scraped: int = 0

    async def init_product_categories(self):
        """Fills `self.categories`."""
        async with self.session.get("https://www.fairprice.com.sg") as res:
            print("Fetched FairPrice homepage")

            # Parse the response payload as a Beautiful Soup document
            soup = bs4.BeautifulSoup(await res.read(), features="html.parser")

            # Get the script tag containing the site's Next props
            next_data_tag = soup.find(id="__NEXT_DATA__")
            assert isinstance(next_data_tag, bs4.Tag)

            # Get the script's string contents
            next_data = next_data_tag.string
            assert next_data is not None

            raw_categories = json.loads(next_data)["props"]["categories"][0]

            print("Parsed Next data")

            for top_cat in raw_categories:
                for sub_cat in top_cat["menu"]:
                    slug = sub_cat["url"].split("/")[-1]
                    self.categories[slug] = sub_cat["name"]

    async def scrape(self):
        """Scrapes all the products from the FairPrice API and writes the scraped data to the database."""
        tasks = [self.scrape_category(cat) for cat in self.categories.keys()]
        await asyncio.gather(*tasks)

    async def scrape_category(self, category: str):
        """Scrapes data from one category of the API and writes it to the database."""

        total_pages = await self.scrape_page(category, 1)

        # Scrape all the other pages in parallel
        tasks = [self.scrape_page(category, i) for i in range(2, total_pages + 1)]
        await asyncio.gather(*tasks)

    async def scrape_page(
        self,
        category_slug: str,
        page: int,
    ) -> int:
        """
        Scrapes data from one page of the API and writes it to the database.
        Returns the total number of pages in the specified category.
        """
        # Get the URL of the page on the API
        endpoint = self.api_url(category_slug, page)

        # Get the data from the API
        async with self.session.get(endpoint) as res:
            body = await res.json()

        # Gets current page to show progress
        curr_page = body["data"]["pagination"]["page"]

        # Get total pages in the category
        total_pages = body["data"]["pagination"]["total_pages"]

        # Print current progress
        self.products_discovered += len(body["data"]["product"])
        print(
            f"\rScraped {self.products_scraped} of {self.products_discovered} discovered products",
            end="",
        )

        # Gets product information from the response
        tasks = [
            self.extract_product(p, category_slug) for p in body["data"]["product"]
        ]

        await asyncio.gather(*tasks)

        return total_pages

    async def extract_product(
        self,
        product: dict,
        category_slug,
    ):
        """
        Given a raw product dictionary supplied by the FairPrice API,
        extracts the necessary information and writes it to the database.
        """
        # Get product name
        name = product["name"]

        # Get the product's category name
        category = self.categories[category_slug]

        # Get product barcode
        barcodes: list[str] = product["barcodes"] or []

        image = None

        # Get product image
        if product["images"] is not None:
            async with self.session.get(product["images"][0]) as res:
                image = await res.read()

        # Adds product to database
        self.db.create_default_product(
            name,
            category,
            [int(b) for b in barcodes],
            None,
        )

        self.products_scraped += 1

    def api_url(
        self,
        product_category: str,
        page_number=1,
    ) -> str:
        """Returns the URL of the FairPrice API endpoint."""
        return (
            "https://website-api.omni.fairprice.com.sg/api/product/v2"
            f"?pageType=category&url={product_category}&page={page_number}"
        )


async def main():
    """Runs the scraper."""
    db = DatabaseClient("src/client/static", "server-store")

    async with aiohttp.ClientSession(
        # connector=connector,
    ) as session:
        scraper = Scraper(db, session)
        await scraper.init_product_categories()
        await scraper.scrape()

    db._search.flush_default_index_queue()


asyncio.run(main())
