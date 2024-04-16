#!/usr/bin/env python3
"""Merges forked repositories on GitHub with their respective upstream."""

import concurrent.futures
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
headers = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": GITHUB_USERNAME,
}


def manage_workflows(gh_repo):
    """Manage the workflows of a forked GitHub repository."""
    has_errored = False
    workflows = [workflow for workflow in gh_repo.get_workflows()]
    for workflow in workflows:
        if (
            workflow.state != "disabled_manually"
            and workflow.name != "pages-build-deployment"
        ):
            logger.info(f"Disabling the workflow: {workflow.name}")
            res = requests.put(
                f"https://api.github.com/repos/{GITHUB_USERNAME}/{gh_repo.name}/actions/workflows/{workflow.id}/disable",  # noqa: E501 line too long
                auth=REQUESTS_GITHUB_AUTH,
                headers=headers,
            )
            try:
                res.raise_for_status()
            except requests.exceptions.HTTPError as err:
                logger.error(err)
                has_errored = True

    return has_errored


def manage_branches(gh_repo):
    """Manage the branches of a forked GitHub repository."""
    has_errored = False
    for branch_name in frozenset(
        [
            branch.name
            for branch in gh_repo.parent.get_branches()
            if branch.name != "gh-pages"
        ]
        + [branch.name for branch in gh_repo.get_branches()]
    ):
        upstream_branch = None
        try:
            upstream_branch = gh_repo.parent.get_branch(branch_name)
        finally:
            # keep branches that have a (open) PR to be merged upstream
            if tuple(
                pull
                for pull in gh_repo.parent.get_pulls(
                    head=f"{GITHUB_USERNAME}:{branch_name}"
                )
            ):
                continue
            # Don't track a branch non-existent on the upstream, that is
            # redirected upstream, or is the special GitHub Pages branch.
            elif (
                upstream_branch is None
                or upstream_branch.name != branch_name
                or branch_name == "gh-pages"
            ):
                logger.info(f"Deleting the branch: {branch_name}")
                gh_repo.get_git_ref(f"heads/{branch_name}").delete()
                continue

        try:
            gh_repo.get_branch(branch_name)
        except GithubException:
            logger.info(f"Creating the branch: {branch_name}")
            gh_repo.create_git_ref(
                f"refs/heads/{branch_name}",
                gh_repo.parent.get_git_ref(f"heads/{branch_name}").object.sha,
            )
        else:
            logger.info(f"Syncing the branch: {branch_name}")
            res = requests.post(
                f"https://api.github.com/repos/{GITHUB_USERNAME}/{gh_repo.name}/merge-upstream",  # noqa: E501 line too long
                auth=REQUESTS_GITHUB_AUTH,
                headers=headers,
                json={"branch": branch_name},
            )
            try:
                res.raise_for_status()
            except requests.exceptions.HTTPError as err:
                # merge conflict
                if res.status_code == 409:
                    gh_repo.get_git_ref(f"heads/{branch_name}").delete()
                logger.error(f"{err} branch: {branch_name}")
                has_errored = True

    return has_errored


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
    forked_repos = tuple(
        gh.get_repo(f"{GITHUB_USERNAME}/{forked_repo_name}")
        for forked_repo_name in FORKED_REPO_NAMES
    )
    updated_successfully = True
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = []
        for forked_repo in forked_repos:
            logger.info(
                f"Processing the forked repository (branches): {forked_repo.full_name}"  # noqa: E501 line too long
            )
            futures.append(executor.submit(manage_branches, forked_repo))
        for future in concurrent.futures.as_completed(futures):
            if future.result():
                updated_successfully = False

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = []
        for forked_repo in forked_repos:
            logger.info(
                f"Processing the forked repository (workflows): {forked_repo.full_name}"  # noqa: E501 line too long
            )
            futures.append(executor.submit(manage_workflows, forked_repo))
        for future in concurrent.futures.as_completed(futures):
            if future.result():
                updated_successfully = False

    if not updated_successfully:
        sys.exit(1)


if __name__ == "__main__":
    main()
    sys.exit(0)
