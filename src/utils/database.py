"""
This module exposes high-level functions to interface with the
Redis database while abstracting away its architectural details.
"""

import redis
import argon2
import string
import random

r = redis.Redis()
ph = argon2.PasswordHasher()

#### ACCESSING THE APPLICATION ####


def login_is_valid(email: str, password: str) -> bool:
    """
    Returns `True` if the user exists in the database
    and the password matches. Returns `False` otherwise.
    """
    hashed_pw = r.get(f"user:{email}:auth")

    if hashed_pw is None:
        return False

    try:
        return ph.verify(hashed_pw, password)
    except argon2.exceptions.VerifyMismatchError:
        return False


def create_user(name: str, email: str, password: str) -> bool:
    """
    Creates a user in the database. Returns `False` if the user's email
    already exists in the database, and `True` otherwise. A return value
    of `True` can be taken to mean that the operation was successful.
    """
    if r.get(f"user:{email}:auth") is not None:
        return False

    r.set(f"user:{email}:name", name)
    r.set(f"user:{email}:auth", password)

    return True


def create_session(email: str) -> str:
    """
    Creates and returns a session ID for the specified user.
    """
    chars = string.ascii_letters + string.digits
    session_id = "".join(random.choices(chars, k=20))
    r.hset("pending-sessions", session_id, email)

    return session_id


def begin_session(session_id: str) -> str:
    """
    Removes the session ID from the database to prevent the same session from
    being accessed again. Returns the email of the user whose session it is.
    """
    email = str(r.hget("pending-sessions", session_id))
    r.hdel("pending-sessions", session_id)

    return email
