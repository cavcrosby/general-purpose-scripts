#!/usr/bin/env python3
# Standard Library Imports
import os
import subprocess
import shutil
import datetime
from enum import Enum

# Third Party Imports
import requests

# Local Application Imports


# refers to repo type, public, private, forks, etc...
PAYLOAD = {"type": "public"}
GITHUB_USERNAME = ""
API_TOKEN = ""
TEMP_DIR = os.path.basename(f"{os.path.abspath(__file__)}-temp")
GITHUB_LICENSE_API_URL = "https://api.github.com/licenses"
GITHUB_REPOS_API_URL = "https://api.github.com/repos/"
GITHUB_USER_REPO_API_URL = "https://api.github.com/user/repos"


class License(Enum):

    # NOTE: the representation in this case will be the license json from GitHub
    # https://docs.github.com/en/free-pro-team@latest/rest/reference/licenses

    MIT = [
        license
        for license in requests.get(GITHUB_LICENSE_API_URL).json()
        if license["key"] == "mit"
    ][0]
    # GPL3 = [license for license in requests.get(GITHUB_LICENSE_API_URL).json() if license["key"] == "gpl-3.0"][0]

    def equals(self, license):

        return self.value["key"] == license["key"]


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


# will only update licenses on repos that
# have this particular type of license
LICENSE_TO_UPDATE = License.MIT
NEW_LICENSE_FILEPATH = f"{os.getcwd()}/LICENSE"
AUTH = GitHubAuth(API_TOKEN)

os.mkdir(TEMP_DIR)
shutil.copy(NEW_LICENSE_FILEPATH, TEMP_DIR)
os.chdir(TEMP_DIR)

repos = [
    repo
    for repo in requests.get(
        GITHUB_USER_REPO_API_URL, auth=AUTH, params=PAYLOAD
    ).json()
    if not repo["fork"]
]

# create local repos from remotes
for repo in repos:
    subprocess.run(["git", "clone", repo["svn_url"], repo["name"]])
    os.chdir(repo["name"])
    # you can have different licenses for each branch, but why?? No!
    if repo["license"] and LICENSE_TO_UPDATE.equals(repo["license"]):
        # NOTE: only going to work with the default branch from remote repos
        repo_license_filename = requests.get(
            f"{GITHUB_REPOS_API_URL}{GITHUB_USERNAME}/{repo['name']}/license",
            auth=AUTH,
        ).json()["name"]
        # copy in new license and timestamp the commit
        datetimeobj = datetime.datetime.now()
        shutil.copy(NEW_LICENSE_FILEPATH, repo_license_filename)
        subprocess.run(["git", "add", f"{repo_license_filename}"])
        subprocess.run(
            [
                "git",
                "commit",
                "-m",
                f"Update LICENSE {datetimeobj.strftime('%d-%b-%Y')}",
            ]
        )
        subprocess.run(["git", "push"])
    os.chdir("..")

os.chdir("..")
shutil.rmtree(TEMP_DIR)
