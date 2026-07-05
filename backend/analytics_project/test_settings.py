import os

os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("SECRET_KEY", "test-secret-key")

from .settings import *  # noqa: F401, F403
import dj_database_url

_db_url = os.environ.get("DATABASE_URL")
if _db_url:
    _is_remote = "localhost" not in _db_url and "127.0.0.1" not in _db_url
    DATABASES = {
        "default": dj_database_url.parse(
            _db_url,
            conn_max_age=600,
            ssl_require=_is_remote,
            conn_health_checks=True,
        )
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "test.sqlite3",
        }
    }

# Fast hashing in tests
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
