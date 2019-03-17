
import secrets

USERS = {"123": "billy"}


def get_user(token):
    return USERS[token]


def claim_user(user):
    if user in USERS:
        raise ValueError
    token = secrets.token_hex(5)
    USERS[token] = user
    return token
