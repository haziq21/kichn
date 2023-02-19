"""
This module manages the Redis and Meilisearch processes in addition to the web server.
Authored by Haziq Hairil.
"""

from pathlib import Path
import subprocess as sp
import shutil
import time


def main():
    # Get the absolute filepath of the server-store directory
    server_store_dir = (Path(__file__) / "../../../server-store").resolve()
    # Create the server-store directory if it doesn't already exist
    server_store_dir.mkdir(exist_ok=True)

    # Locate the Redis executable
    redis_path = shutil.which("redis-stack-server")

    if redis_path is None:
        print("You don't seem to have Redis Stack installed (or it's not on PATH).")
        print("Please follow the setup instructions in the README.")
        return

    # The RedisJSON module should be in here
    # The first .resolve() resolves any symlinks, and the second resolves the ../..
    redis_modules_dir = (Path(redis_path).resolve() / "../../lib").resolve()

    # Start the Redis server as a subprocess
    redis_proc = sp.Popen(
        [
            "redis-server",
            # Config: write Redis dump to server-store
            "--dir",
            server_store_dir,
            # Config: load the RedisJSON module
            "--loadmodule",
            redis_modules_dir / "rejson.so",
        ],
        # Redirect info text to /dev/null so we don't see it on the terminal
        stdout=sp.DEVNULL,
    )

    # Start the Meilisearch server as a subprocess
    meilisearch_proc = sp.Popen(
        [
            "meilisearch",
            # Config: write Meilisearch database files to server-store
            "--db-path",
            server_store_dir / "data.ms",
            # Config: write Meilisearch dump to server-store
            "--dumps-dir",
            server_store_dir / "dumps.ms",
        ],
        # Meilisearch outputs normal info text to stderr instead of stdout
        stderr=sp.DEVNULL,
    )

    # 100ms should be enough for Redis and Meilisearch to start running
    time.sleep(0.1)

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
        # `redis_proc.terminate()` doesn't seem to work sometimes
        sp.run(["redis-cli", "shutdown"])
        return

    try:
        # Run the web server
        import server
    finally:
        # Terminate the Redis and Meilisearch servers when the web server is killed
        # `redis_proc.terminate()` doesn't seem to work sometimes
        sp.run(["redis-cli", "shutdown"])
        meilisearch_proc.terminate()


main()
