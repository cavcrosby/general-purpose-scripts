#!/usr/bin/env python3
"""Merges forked repositories on GitHub with their respective upstream."""

from configs import (
    GITHUB_USERNAME,
    GITHUB_ACCESS_TOKEN,
    REQUESTS_GITHUB_AUTH,
)
from github import Github, Auth
from github.GithubException import GithubException
import logging
import os
import requests
import sys

FORKED_REPO_NAMES = [
    "mrepo",
    "The-Stolen-Crown-RPG",
    "community.general",
    "vagrant",
    "shunit2",
    "google-styleguide",
    "packer",
    "ansible",
    "flake8-docstrings",
    "moby",
    "lxd",
    "docker-cli",
    "kubernetes-website",
    "jaxlug.github.io",
    "ansible-documentation",
    "vagrant-libvirt",
    "papirus-icon-theme",
    "pyenv",
    "tigera-operator",
    "calico",
    "awesome-python",
    "xv6-public",
]

logger = logging.getLogger(__name__)


def main():
    """Start the main program execution."""
    logging.basicConfig(
        level=(
            os.getenv("LOGLEVEL")
            if os.getenv("LOGLEVEL")
            # use default root logger level
            else logging.getLogger().getEffectiveLevel()
        )
    )
    gh = Github(auth=Auth.Token(GITHUB_ACCESS_TOKEN))
    updated_successfully = True
    for forked_repo_name in FORKED_REPO_NAMES:
        repo = gh.get_repo(f"{GITHUB_USERNAME}/{forked_repo_name}")
        logger.info(f"Processing the forked repository: {repo.full_name}")
        for branch_name in frozenset(
            [
                branch.name
                for branch in repo.parent.get_branches()
                if branch.name != "gh-pages"
            ]
            + [branch.name for branch in repo.get_branches()]
        ):
            upstream_branch = None
            try:
                upstream_branch = repo.parent.get_branch(branch_name)
            finally:
                # Don't track a branch non-existent on the upstream, that is
                # redirected upstream, or is the special GitHub Pages branch.
                if (
                    upstream_branch is None
                    or upstream_branch.name != branch_name
                    or branch_name == "gh-pages"
                ):
                    logger.info(f"Deleting the branch: {branch_name}")
                    repo.get_git_ref(f"heads/{branch_name}").delete()
                    continue

            try:
                repo.get_branch(branch_name)
            except GithubException:
                logger.info(f"Creating the branch: {branch_name}")
                repo.create_git_ref(
                    f"refs/heads/{branch_name}",
                    repo.parent.get_git_ref(f"heads/{branch_name}").object.sha,
                )
            else:
                logger.info(f"Syncing the branch: {branch_name}")
                headers = {
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                    "User-Agent": GITHUB_USERNAME,
                }
                res = requests.post(
                    f"https://api.github.com/repos/{GITHUB_USERNAME}/{forked_repo_name}/merge-upstream",  # noqa: E501 line too long
                    auth=REQUESTS_GITHUB_AUTH,
                    headers=headers,
                    json={"branch": branch_name},
                )
                try:
                    res.raise_for_status()
                except requests.exceptions.HTTPError as err:
                    # merge conflict
                    if res.status_code == 409:
                        repo.get_git_ref(f"heads/{branch_name}").delete()
                    logger.error(f"{err} branch: {branch_name}")
                    updated_successfully = False

        workflows = [workflow for workflow in repo.get_workflows()]
        for workflow in workflows:
            if (
                workflow.state != "disabled_manually"
                and workflow.name != "pages-build-deployment"
            ):
                logger.info(f"Disabling the workflow: {workflow.name}")
                res = requests.put(
                    f"https://api.github.com/repos/{GITHUB_USERNAME}/{forked_repo_name}/actions/workflows/{workflow.id}/disable",  # noqa: E501 line too long
                    auth=REQUESTS_GITHUB_AUTH,
                    headers=headers,
                )
                try:
                    res.raise_for_status()
                except requests.exceptions.HTTPError as err:
                    logger.error(err)
                    updated_successfully = False

    if not updated_successfully:
        sys.exit(1)


if __name__ == "__main__":
    main()
    sys.exit(0)
