#!/usr/bin/env python3
"""Merges forked repos on GitHub with their respective upstream."""
# Standard Library Imports
import argparse
import json
import os
import shutil
import subprocess
import sys

# Third Party Imports
import git

# Local Application Imports
import keys
import pylib

# constants and other program configurations
_TEMP_DIR = os.path.basename(f"{os.path.abspath(__file__)}-temp")
_arg_parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=lambda prog: pylib.argparse.CustomHelpFormatter(
        prog, max_help_position=35
    ),
    allow_abbrev=False,
)

REMOTE_NAME = "forked-repo"

# positional and option arg labels
# used at the command line and to reference values of arguments

VERBOSE_SHORT_OPTION = "v"
VERBOSE_LONG_OPTION = "verbose"


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
            f"-{VERBOSE_SHORT_OPTION}",
            f"--{VERBOSE_LONG_OPTION}",
            action="store_true",
            help="increase verbosity",
        )

        args = vars(_arg_parser.parse_args())
        return args
    except SystemExit:
        sys.exit(1)


def main(args):
    """Start the main program execution."""
    configs = json.loads(sys.stdin.buffer.read().decode("utf-8").strip())
    if not configs:
        configs = json.loads(
            subprocess.run(
                ["genconfigs", "--export"],
                capture_output=True,
                encoding="utf-8",
                check=True,
            ).stdout.strip()
        )
    webhosted_git_account_url = configs[keys.WEBHOSTED_GIT_ACCOUNT_URL_KEY]
    forked_repo_to_upstream_urls = configs[
        keys.FORKED_REPOS_TO_UPSTREAM_URLS_KEY
    ]
    os.mkdir(_TEMP_DIR)
    os.chdir(_TEMP_DIR)
    if args[VERBOSE_LONG_OPTION]:
        git_clone_cmd = ("git", "clone", "--verbose")
        git_branch_cmd = ("git", "branch", "--verbose", "--track")
        git_push_cmd = ("git", "push", "--verbose")
    else:
        git_clone_cmd = ("git", "clone", "--quiet")
        git_branch_cmd = ("git", "branch", "--quiet", "--track")
        git_push_cmd = ("git", "push", "--quiet")

    for forked_repo, upstream_url in forked_repo_to_upstream_urls.items():
        upstream_repo_name = os.path.basename(upstream_url)
        subprocess.run(
            git_clone_cmd + (upstream_url, upstream_repo_name),
            encoding="utf-8",
            check=True,
        )
        os.chdir(upstream_repo_name)

        # sequence of commands inspired from:
        # https://stackoverflow.com/questions/15779740/how-to-update-my-fork-to-have-the-same-branches-and-tags-as-the-original-reposit
        # https://stackoverflow.com/questions/379081/track-all-remote-git-branches-as-local-branches/6300386#answer-27234826
        upstream_repo = git.Repo(os.getcwd())
        upstream_repo.create_remote(
            name=REMOTE_NAME,
            url=os.path.join(webhosted_git_account_url, forked_repo),
        )
        for short_refname in upstream_repo.remote().refs:
            try:
                _ = subprocess.run(
                    git_branch_cmd
                    + (short_refname.remote_head, short_refname.name),
                    capture_output=True,
                    encoding="utf-8",
                    check=True,
                )
            except subprocess.SubprocessError:
                # Will occur if creating local branch name set to 'HEAD' or
                # to the same default branch name.
                continue
        subprocess.run(
            git_push_cmd + ("--all", REMOTE_NAME),
            encoding="utf-8",
            check=True,
        )
        subprocess.run(
            git_push_cmd + ("--tags", REMOTE_NAME),
            encoding="utf-8",
            check=True,
        )
        subprocess.run(
            ("disable_github_actions.py", forked_repo),
            encoding="utf-8",
            check=True,
        )
        os.chdir("..")
    os.chdir("..")
    shutil.rmtree(_TEMP_DIR)


if __name__ == "__main__":
    args = retrieve_cmd_args()
    main(args)
    sys.exit(0)
