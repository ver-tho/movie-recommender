import os
import hashlib


ACCOUNTS_FILE = "accounts.txt"


def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def username_exists(username: str) -> bool:
    if not os.path.exists(ACCOUNTS_FILE):
        return False
    with open(ACCOUNTS_FILE, "r") as f:
        for line in f:
            parts = line.strip().split(",")
            if parts and parts[0] == username:
                return True
    return False


def create_account(username: str, password: str) -> tuple[bool, str]:
    if not username or not password:
        return False, "Username and password cannot be empty."
    if "," in username or "," in password:
        return False, "Username and password cannot contain commas."
    if username_exists(username):
        return False, "This username already exists. Choose a different one."
    with open(ACCOUNTS_FILE, "a") as f:
        f.write(f"{username},{_hash(password)}\n")
    return True, "Account created successfully!"


def login(username: str, password: str) -> tuple[bool, str]:
    if not os.path.exists(ACCOUNTS_FILE):
        return False, "No accounts found. Please create an account first."
    hashed = _hash(password)
    with open(ACCOUNTS_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(",")
            if len(parts) < 2:
                continue
            stored_user, stored_pass = parts[0], parts[1]
            if username == stored_user:
                if hashed == stored_pass:
                    return True, "Login successful!"
                return False, "Incorrect password."
    return False, "Username not found."


def save_watched_movies(username: str, watched: list[str]) -> None:
    filename = f"{username}_watched.txt"
    with open(filename, "w") as f:
        for title in watched:
            f.write(title + "\n")


def load_watched_movies(username: str) -> list[str]:
    filename = f"{username}_watched.txt"
    if not os.path.exists(filename):
        return []
    with open(filename, "r") as f:
        return [line.strip() for line in f if line.strip()]
