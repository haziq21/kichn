"""
This module manages the Redis and Meilisearch processes in addition to the web server.
Authored by Haziq Hairil.
"""

import subprocess as sp
import time
from pathlib import Path


def main():
    # Get the absolute filepath of the server-store directory
    server_store_dir = (Path(__file__) / "../../../server-store").resolve()

    # Start the Redis server as a subprocess
    redis_proc = sp.Popen(
        [
            "redis-stack-server",
            "--dir",
            server_store_dir,
        ],
        stdout=sp.DEVNULL,
    )

    # Start the Meilisearch server as a subprocess
    meilisearch_proc = sp.Popen(
        [
            "meilisearch",
            "--db-path",
            server_store_dir / "data.ms",
            "--dumps-dir",
            server_store_dir / "dumps.ms"
        ],
        # Meilisearch outputs normal info text to stderr instead of stdout
        stderr=sp.DEVNULL,
    )

    # 50ms should be enough for Redis and Meilisearch to start running
    time.sleep(0.05)

    # Check that Redis was able to start successfully
    if redis_proc.poll():
        print("Redis exited with a non-zero exit code.")
        print("Check that there is no other Redis instance running.")
        print("\nTo terminate a Redis instance, run")
        print("  $ redis-cli SHUTDOWN")

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
    finally:
        # Terminate the Redis and Meilisearch servers when the web server is killed
        redis_proc.terminate()
        meilisearch_proc.terminate()


main()
