# Kichn

Kichn is a kitchen inventory tracker and grocery list webapp. This is a school project.

## Usage & features

- Users can have multiple *kitchens*, and each kitchen has a *inventory list* (the stuff you have in your kitchen) and a *grocery list* (the stuff you need to buy).
- Add items to the grocery list by searching for it by name or barcode.
- *Buy* a grocery list item (and optionally set an expiry date) to move it to the inventory list.
- *Use* an inventory list item to remove it from the inventory list (or move it to the grocery list).

>  All the products available on Kichn are scraped from FairPrice's (reverse-engineered / not publicly documented) API.

## Setting up

On a Mac, install all software dependencies with [Homebrew](https://brew.sh/).

```
$ brew tap redis-stack/redis-stack
$ brew install redis-stack-server meilisearch zbar
```

And install all the Python dependencies from `requirements.txt`.

```
$ pip install -r requirements.txt
```

## Running

Run all commands from the project root folder (`cd` into the project root folder first).

To run the web server:

```
$ python3 src/server/main.py
```

This also starts the Redis and Meilisearch servers. Note that the product database will initially be empty.

Once `main.py` is running, you can run the FairPrice API scraper:

```
$ python3 src/server/scraper.py
```

This will scrape FairPrice's API and populate Kichn's product database.

## Techstack

Here's a breakdown of the libraries and softwares that we've used in this project.

### Server

- [Redis](https://redis.io/) as a main and cache database
- [Meilisearch](https://www.meilisearch.com/) as a full-text search engine
- [AIOHTTP](https://docs.aiohttp.org/en/stable/) as a minimalist web server framework
- [Jinja](https://jinja.palletsprojects.com/en/3.1.x/) as a HTML templating engine
- [ZBar](https://zbar.sourceforge.net/) as a barcode reader

### Client

- [HTMX](https://htmx.org/) as a SSR-first HTML framework
- [AlpineJS](https://alpinejs.dev/) as a JS framework
- [Windi CSS](https://windicss.org/) as a CSS framework
