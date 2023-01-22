import subprocess as sp
import time


def main():
    # Start the Redis server as a subprocess
    redis_proc = sp.Popen(
        ["redis-server", "redis.conf"],
        stdout=sp.DEVNULL,
    )

    # Start the Meilisearch server as a subprocess
    meilisearch_proc = sp.Popen(
        ["meilisearch"],
        # Meilisearch outputs normal info text to stderr instead of stdout
        stderr=sp.DEVNULL,
    )

    # 50ms should be enough for Redis and Meilisearch to start running
    time.sleep(0.05)

    # Check that Redis was able to start successfully
    if redis_proc.poll():
        print("Redis exited with a non-zero exit code.")
        print("Check that you don't already have another Redis instance running.")

        # Terminate the Meilisearch server
        meilisearch_proc.terminate()
        return

    # Check that Meilisearch was able to start successfully
    if meilisearch_proc.poll():
        print("Meilisearch exited with a non-zero exit code.")
        print("Check that you don't already have another Meilisearch instance running.")

        # Terminate the Redis server
        redis_proc.terminate()
        return

    try:
        # Run the web server
        import server
    except KeyboardInterrupt:
        # Terminate the Redis and Meilisearch servers when the web server is killed
        redis_proc.terminate()
        meilisearch_proc.terminate()


main()
