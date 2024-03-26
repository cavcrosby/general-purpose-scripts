"""Configuration loader for the Python scripts."""

import os
from requests.auth import AuthBase

GITHUB_USERNAME = "cavcrosby"
GITHUB_API_KEY = os.getenv("GITHUB_API_KEY", "")


class TokenAuth(AuthBase):
    """Implements a token authentication scheme."""

    def __init__(self, token):
        """Instantiate TokenAuth class."""
        self.token = token

    def __call__(self, request):
        """Attach an API token to the Authorization header."""
        request.headers["Authorization"] = f"Bearer {self.token}"
        return request


REQUESTS_GITHUB_AUTH = TokenAuth(GITHUB_API_KEY)
