#!/usr/bin/env python3
# Standard Library Imports
import sys

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


# this will be the git repo whose
# github actions will be deleted from
try:
    REPO = sys.argv[1]
except IndexError:
    print(f"Usage: {sys.argv[0]} GIT_REPO_NAME")
    sys.exit(1)
OWNER = ""
API_TOKEN = ""
WORKFLOW_ID_PLACEHOLDER = "WORKFLOW_ID"
PAYLOAD = {"type": "all"}
GITHUB_REPO_WORKFLOWS_URL = (
    f"https://api.github.com/repos/{OWNER}/{REPO}/actions/workflows"
)
GITHUB_REPO_WORKFLOWS_URL_BASE = f"https://api.github.com/repos/{OWNER}/{REPO}/actions/workflows/{WORKFLOW_ID_PLACEHOLDER}/disable"

auth = GitHubAuth(API_TOKEN)

workflows = requests.get(
    GITHUB_REPO_WORKFLOWS_URL, auth=auth, params=PAYLOAD
).json()

if workflows["total_count"] > 0:
    for workflow in workflows["workflows"]:
        github_repo_workflows_disable_url = GITHUB_REPO_WORKFLOWS_URL_BASE.replace(
            WORKFLOW_ID_PLACEHOLDER, str(workflow["id"])
        )
        requests.put(github_repo_workflows_disable_url, auth=auth)
sys.exit(0)
