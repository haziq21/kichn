# Kichn

Kichn is a kitchen inventory tracker and grocery list webapp. Documentation about the APIs provided by the web server is included in the `docs` folder. This is a school project.

## Setting up

On a Mac, install all software dependencies with [Homebrew](https://brew.sh/).

```
$ brew install redis meilisearch zbar
```

And install all the Python dependencies from `requirements.txt`.

```
$ pip install -r requirements.txt
```

## Running

Run all commands from the project root folder (`cd` into the project root folder first). In separate shell sessions, start the Redis and Meilisearch servers.

```
$ redis-server redis.conf
```

```
$ meilisearch
```

To run the web server:

```
$ python3 src/server/server.py
```

To run the FairPrice API scraper:

```
$ python3 src/server/scraper.py
```
