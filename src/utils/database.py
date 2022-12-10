"""
This module exposes high-level functions to interface with the
Redis database while abstracting away its architectural details.

Authored by Haziq Hairil.
"""

import redis
import argon2
import string
import random

# TODO: Move these into a DB class
_r = redis.Redis()
_ph = argon2.PasswordHasher()


def _gen_random_id(k=20) -> str:
    """
    Returns a randomly-generated string of k letters and digits.
    """
    sample_chars = string.ascii_letters + string.digits
    return "".join(random.choices(sample_chars, k=k))


#### BUILDING THE DEFAULT DATABASE ####


def create_default_product(name: str, category: str, barcodes: list[int]) -> str:
    """
    Creates a new default product in the database.
    Returns the generated ID of the product.
    """
    product_id = _gen_random_id()

    # Write the product data to the database
    _r.set(f"product:{product_id}:name", name)
    _r.set(f"product:{product_id}:category", category)
    _r.hset("barcodes", mapping={str(b): product_id for b in barcodes})

    return product_id


#### ACCESSING THE APPLICATION ####


def login_is_valid(email: str, password: str) -> bool:
    """
    Returns `True` if the user exists in the database
    and the password matches. Returns `False` otherwise.
    """
    hashed_pw = _r.get(f"user:{email}:auth")

    if hashed_pw is None:
        # User does not exist
        return False

    try:
        # User exists and password is correct
        return _ph.verify(hashed_pw, password)
    except argon2.exceptions.VerifyMismatchError:
        # Password is incorrect
        return False


def create_user(name: str, email: str, password: str) -> bool:
    """
    Creates a user in the database. Returns `False` if the user's email
    already exists in the database, and `True` otherwise. A return value
    of `True` can be taken to mean that the operation was successful.
    """
    if _r.get(f"user:{email}:auth") is not None:
        # User already exists
        return False

    # Write the user's account data to the database
    _r.set(f"user:{email}:name", name)
    _r.set(f"user:{email}:auth", _ph.hash(password))

    return True


def create_session(email: str) -> str:
    """
    Creates and returns a session token for the specified user.
    """
    session_token = _gen_random_id()
    _r.hset("pending-sessions", session_token, email)

    return session_token


def begin_session(session_token: str) -> str:
    """
    Removes the session token from the database to prevent the same session from
    being accessed again. Returns the email of the user whose session it is.
    Raises an AssertionError if the session token does not exist in the database.
    """
    email_bytes = _r.hget("pending-sessions", session_token)
    assert email_bytes is not None

    # Delete the session from the database
    _r.hdel("pending-sessions", session_token)

    return str(email_bytes)


#### MODIFYING KITCHENS ####


def create_kitchen(email: str, kitchen_name: str) -> str:
    """
    Creates a new kitchen and assigns the indicated
    user as the owner. Returns the kitchen's ID.
    """
    kitchen_id = _gen_random_id()

    # Write the kitchen data to the database
    _r.set(f"kitchen:{kitchen_id}:name", kitchen_name)
    _r.sadd(f"user:{email}:owned-kitchens", kitchen_id)

    return kitchen_id


def rename_kitchen(kitchen_id: str, new_name: str):
    """
    Sets the name of the kitchen to `new_name`.
    """
    _r.set(f"kitchen:{kitchen_id}:name", new_name)


def delete_kitchen(kitchen_id: str):
    """
    Deletes the kitchen from the database.
    """
    # TODO: Remember to delete the kitchen ID from users' owned-kitchens and shared-kitchens
    # Get all the Redis keys belonging to the specified kitchen
    kitchen_keys = _r.keys(f"kitchen:{kitchen_id}:*")
    # Delete the keys
    _r.delete(*kitchen_keys)
