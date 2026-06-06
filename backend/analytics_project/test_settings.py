from .settings import *  # noqa: F401, F403

# Use local PostgreSQL for tests (pytest-django creates test_ctomop_dev)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "ctomop_dev",
        "USER": "postgres",
        "HOST": "localhost",
    }
}

# Fast hashing in tests
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
