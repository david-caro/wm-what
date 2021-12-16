from functools import wraps

from flask import session, url_for


def logged_in(fn):
    @wraps(fn)
    def _inner(*args, **kwargs):
        user = session.get("username")
        if not session.get("username"):
            return (f"Unauthorized, you might want to login first (<a href=\"{url_for('login')}\")> here</a>", 401)

        kwargs["user"] = user
        return fn(*args, **kwargs)

    return _inner
