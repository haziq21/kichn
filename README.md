# Kichn

Kichn is a kitchen inventory tracker and grocery list app.

## Setting up

On a Mac, install Redis Stack using [Homebrew](https://brew.sh/) (or follow any other method listed on the [Redis Stack installation page](https://redis.io/docs/stack/get-started/install/)).

```
$ brew tap redis-stack/redis-stack
$ brew install redis-stack
```

Then install ZBar.

```
$ brew install zbar
```

And finally, install all the Python dependencies from `requirements.txt`.

```
$ pip install -r requirements.txt
```

## Running

Run all commands from the project root folder (`cd` into the project root folder first).

### Client

Multiple clients can connect to the same server.

```
$ python3 src/client.py
```

### Server

Start up the Redis database first (this assumes `redis-stack-server` is on your PATH).

```
$ redis-stack-server
```

To run the web server:

```
$ python3 src/server.py
```

To run the FairPrice API scraper:

```
$ python3 src/scraper.py
```

