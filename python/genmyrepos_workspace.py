#!/usr/bin/env python3
"""Generates a "Multi-root" vscode code-workspace file containing my repos."""
# Standard Library Imports
import argparse
import json
import os
import pathlib
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

GIT_REPOS_PATH = os.environ["GIT_REPOS_PATH"]
MYREPOS_WORKSPACE_FILE = "myrepos.code-workspace"
MYREPOS_WORKSPACE_FILE_PATH = os.path.join(
    GIT_REPOS_PATH, MYREPOS_WORKSPACE_FILE
)
# per_page may need to increase overtime as I create/fork new repos
PAYLOAD = {"type": "all", "per_page": 100}
GITHUB_USER_REPOS_API_URL = "https://api.github.com/user/repos"

# configuration keys

FOLDERS_KEY = "folders"

# positional and option arg labels
# used at the command line and to reference values of arguments

STDIN_SHORT_OPTION = "s"
STDIN_LONG_OPTION = "stdin"

workspace_datastructure = {FOLDERS_KEY: list()}


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
    auth = pylib.githubauth.GitHubAuth(configs[keys.GITHUB_API_TOKEN_KEY])
    repos = requests.get(GITHUB_USER_REPOS_API_URL, auth=auth, params=PAYLOAD)
    if repos.status_code == 401:
        raise requests.HTTPError(
            "unable to access GitHub API with stored api token"
        )

    repo_names = [repo["name"] for repo in repos.json() if not repo["fork"]]
    for repo_name in repo_names:
        repo_path = os.path.join(GIT_REPOS_PATH, repo_name)
        if pathlib.Path(repo_path).exists():
            workspace_datastructure[FOLDERS_KEY].append({"path": repo_path})

    pathlib.Path(GIT_REPOS_PATH).mkdir(parents=True, exist_ok=True)
    with open(MYREPOS_WORKSPACE_FILE_PATH, "w") as file:
        json.dump(workspace_datastructure, file, indent=4)


if __name__ == "__main__":
    args = retrieve_cmd_args()
    main(args)
    sys.exit(0)
