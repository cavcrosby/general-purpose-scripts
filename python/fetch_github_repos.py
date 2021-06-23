#!/usr/bin/env python3
# Standard Library Imports
import subprocess

# Third Party Imports
import requests

# Local Application Imports


# you can ignore this class, API_TOKEN is used for authentication
class GitHubAuth(requests.auth.AuthBase):
    """Custom HTTPBasicAuth for GitHub.

    GitHub does not require a username
    and password to use their API. Instead
    an API token is used.

    Parameters
    ----------
    API_TOKEN : str
        Assigned when an instance is created.

    """

    def __init__(self, API_TOKEN):

        self.API_TOKEN = API_TOKEN

    def __call__(self, requests_obj):

        requests_obj.headers["Authorization"] = self.auth_header_value()
        return requests_obj

    def auth_header_value(self):
        """Part of OAuth2 authentication.
        
        See the following link:
        https://developer.github.com/v3/#oauth2-token-sent-in-a-header

        """
        return f"token {self.API_TOKEN}"


API_TOKEN = ""
PAYLOAD = {"type": "all"}
GITHUB_API_URL = "https://api.github.com/user/repos"

auth = GitHubAuth(API_TOKEN)

repos = requests.get(GITHUB_API_URL, auth=auth, params=PAYLOAD)
repo_names_to_urls = {repo["name"]: repo["svn_url"] for repo in repos.json()}

for repo_name in repo_names_to_urls:
    subprocess.run(["git", "clone", repo_names_to_urls[repo_name], repo_name])
