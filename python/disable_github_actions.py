#!/usr/bin/env python3
"""Disables all workflows associated with GitHub repos' actions."""
# Standard Library Imports
import argparse
import json
import os
import subprocess
import sys

# Third Party Imports
import requests

# Local Application Imports
import keys
import pylib


# constants and other program configurations
_PROGRAM_NAME = os.path.basename(os.path.abspath(__file__))
_PROGRAM_ROOT = os.getcwd()
_DESC = __doc__
_arg_parser = argparse.ArgumentParser(
    description=_DESC,
    formatter_class=lambda prog: pylib.argparse.CustomHelpFormatter(
        prog, max_help_position=35
    ),
    allow_abbrev=False,
)

WORKFLOW_ID_PLACEHOLDER = "_WORKFLOW_ID"
REPO_PLACEHOLDER = "_REPO"
PAYLOAD = {"type": "all"}

# positional and option arg labels
# used at the command line and to reference values of arguments

REPO_NAME_POSITIONAL_ARG = "repo_name"


def _retrieve_cmd_args():
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
        _arg_parser.add_argument(
            f"{REPO_NAME_POSITIONAL_ARG}",
            action="append",
            help="represents the github repo name",
            metavar=REPO_NAME_POSITIONAL_ARG.upper(),
        )

        args = vars(_arg_parser.parse_args())
        return args
    except SystemExit:
        sys.exit(1)


def main(args):
    """Start the main program execution."""
    configs = json.loads(
        subprocess.run(
            ["genconfigs.py", "--export"],
            capture_output=True,
            encoding="utf-8",
            check=True,
        ).stdout.strip()
    )
    owner = configs[keys.OWNER_KEY]
    workflows_url = f"https://api.github.com/repos/{owner}/{REPO_PLACEHOLDER}/actions/workflows"
    workflows_disable_url = f"https://api.github.com/repos/{owner}/{REPO_PLACEHOLDER}/actions/workflows/{WORKFLOW_ID_PLACEHOLDER}/disable"
    auth = pylib.githubauth.GitHubAuth(configs[keys.GITHUB_API_TOKEN_KEY])
    repos_to_workflows = {
        repo: requests.get(
            workflows_url.replace(REPO_PLACEHOLDER, repo),
            auth=auth,
            params=PAYLOAD,
        ).json()
        for repo in args[REPO_NAME_POSITIONAL_ARG]
    }
    for repo, workflows in repos_to_workflows.items():
        if workflows["total_count"] > 0:
            for workflow in workflows["workflows"]:
                github_repo_workflows_disable_url = (
                    workflows_disable_url.replace(
                        WORKFLOW_ID_PLACEHOLDER,
                        str(workflow["id"]),
                    ).replace(REPO_PLACEHOLDER, repo)
                )
                requests.put(github_repo_workflows_disable_url, auth=auth)


if __name__ == "__main__":
    args = _retrieve_cmd_args()
    main(args)
    sys.exit(0)
