#!/usr/bin/env python3
"""Disables all workflows associated with GitHub repos' actions."""
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

WORKFLOW_ID_PLACEHOLDER = "__WORKFLOW_ID__"
REPO_PLACEHOLDER = "__REPO__"
PAYLOAD = {"type": "all"}

# positional and option arg labels
# used at the command line and to reference values of arguments

STDIN_SHORT_OPTION = "s"
STDIN_LONG_OPTION = "stdin"


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
        _arg_parser.add_argument(
            f"-{STDIN_SHORT_OPTION}",
            f"--{STDIN_LONG_OPTION}",
            action="store_true",
            help="read the gps configuration from stdin",
        )

        args = vars(_arg_parser.parse_args())
        return args
    except SystemExit:
        sys.exit(1)


def main(args):
    """Start the main program execution."""
    if args[STDIN_LONG_OPTION]:
        configs = json.loads(sys.stdin.buffer.read().decode("utf-8").strip())
    else:
        configs = json.loads(
            subprocess.run(
                ["genconfigs", "--export"],
                capture_output=True,
                encoding="utf-8",
                check=True,
            ).stdout.strip()
        )
    owner = configs[keys.GITHUB_USERNAME_KEY]
    workflows_url = f"https://api.github.com/repos/{owner}/{REPO_PLACEHOLDER}/actions/workflows"
    workflows_disable_url = f"https://api.github.com/repos/{owner}/{REPO_PLACEHOLDER}/actions/workflows/{WORKFLOW_ID_PLACEHOLDER}/disable"
    auth = pylib.githubauth.GitHubAuth(configs[keys.GITHUB_API_TOKEN_KEY])
    repos_to_workflows = {
        repo: requests.get(
            workflows_url.replace(REPO_PLACEHOLDER, repo),
            auth=auth,
            params=PAYLOAD,
        ).json()
        for repo in configs[keys.REPO_NAMES_KEY]
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
    args = retrieve_cmd_args()
    main(args)
    sys.exit(0)
