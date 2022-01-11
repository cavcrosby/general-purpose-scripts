#!/usr/bin/env python3
"""Clones all GitHub repos to the local machine."""
# Standard Library Imports
import argparse
import json
import subprocess
import sys

# Third Party Imports
import requests

# Local Application Imports
import keys
import pylib

# constants and other program configurations
_arg_parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=lambda prog: pylib.argparse.CustomHelpFormatter(
        prog, max_help_position=35
    ),
    allow_abbrev=False,
)

PAYLOAD = {"type": "all"}
GITHUB_API_URL = "https://api.github.com/user/repos"


def retrieve_cmd_args():
    """Retrieve command arguments from the command line.

    Returns
    -------
    Namespace
        An object that holds attributes pulled from the command line.

    Raises
    ------
    SystemExit
        If user input is not considered valid when parsing arguments.

    """
    try:
        args = vars(_arg_parser.parse_args())
        return args
    except SystemExit:
        sys.exit(1)


def main(args):
    """Start the main program execution."""
    configs = json.loads(
        subprocess.run(
            ["genconfigs", "--export"],
            capture_output=True,
            encoding="utf-8",
            check=True,
        ).stdout.strip()
    )
    auth = pylib.githubauth.GitHubAuth(configs[keys.GITHUB_API_TOKEN_KEY])
    repos = requests.get(GITHUB_API_URL, auth=auth, params=PAYLOAD)
    repo_names_to_urls = {
        repo["name"]: repo["html_url"] for repo in repos.json()
    }
    for repo_name in repo_names_to_urls:
        subprocess.run(
            ["git", "clone", repo_names_to_urls[repo_name], repo_name]
        )


if __name__ == "__main__":
    args = retrieve_cmd_args()
    main(args)
    sys.exit(0)
