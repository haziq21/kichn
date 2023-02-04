# Kichn

Kichn is a kitchen inventory tracker and grocery list webapp. This is a school project.

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

This also starts the Redis and Meilisearch servers.

Once `main.py` is running, you can run the FairPrice API scraper:

```
$ python3 src/server/scraper.py
```

## Techstack

Here's a breakdown of the libraries and softwares that we've used in this project.

### Server

- [Redis](https://redis.io/) as a main and cache database
- [Meilisearch](https://www.meilisearch.com/) as a full-text search engine
- [AIOHTTP](https://docs.aiohttp.org/en/stable/) as a minimalist web server framework
- [Jinja](https://jinja.palletsprojects.com/en/3.1.x/) as a HTML templating engine
- [ZBar](https://zbar.sourceforge.net/) as a barcode reader

### Client

- [Windi CSS](https://windicss.org/) as a CSS framework
- [HTMX](https://htmx.org/) as a HTML framework
