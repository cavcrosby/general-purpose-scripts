#!/usr/bin/env python3
"""Updates all of the license files in my GitHub repos."""
# Standard Library Imports
import argparse
import datetime
import enum
import json
import os
import shutil
import subprocess
import sys

# Third Party Imports
import requests

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

PAYLOAD = {"type": "public"}
KEY = "key"
GITHUB_LICENSE_API_URL = "https://api.github.com/licenses"
GITHUB_REPOS_API_URL = "https://api.github.com/repos/"
GITHUB_USER_REPO_API_URL = "https://api.github.com/user/repos"

# positional and option arg labels
# used at the command line and to reference values of arguments

LICENSE_POSITIONAL_ARG = "license"


class License(enum.Enum):
    """The license datatype."""

    # license API reference:
    # https://docs.github.com/en/free-pro-team@latest/rest/reference/licenses
    _LICENSES = requests.get(GITHUB_LICENSE_API_URL).json()
    MIT = [license for license in _LICENSES if license[KEY] == "mit"][0]

    def generate_body(self):
        """Generate the license text.

        Returns
        -------
        str
            The license text.

        """
        license_text = requests.get(self.value["url"]).json()["body"]
        return self._fill_in_body(license_text)

    def _fill_in_body(self, license_text):
        """Take the license text and fill in placeholders.

        Parameters
        ----------
        license_text : str
            The text inside of a license file.

        Returns
        -------
        str
            The license text but with the placeholders filled in.

        """
        mappings = {
            str(License.MIT): license_text.replace(
                "[year]", datetime.datetime.now().strftime("%Y")
            ).replace("[fullname]", "Conner Crosby")
        }
        return mappings[str(self)]

    def __eq__(self, license):
        """Determine if the license is equal to this instance.

        Parameters
        ----------
        license : dict
            A license JSON object obtained using GitHub's API.

        Returns
        -------
        bool
            If the license is equal to this instance.

        """
        return sorted(self.value.items()) == sorted(license.items())

    def __str__(self):
        """Return the string representation of an instance."""
        return self.value[KEY]


def _arg_license_conv(license):
    """Map the friendly license representation to its object form.

    Parameters
    ----------
    license : str
        The friendly representation of the license.

    Returns
    -------
    update_github_repos_license.License
        A license object.

    """
    mappings = {str(License.MIT): License.MIT}
    return mappings[license]


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
            f"{LICENSE_POSITIONAL_ARG}",
            action="append",
            choices=[str(License.MIT)],
            help="the license to update for each repo",
            metavar=LICENSE_POSITIONAL_ARG.upper(),
        )

        args = vars(_arg_parser.parse_args())
        # Type conversions occur before checking inclusion in choices,
        # meaning any conversion will need to occur after parsing args.
        # For reference:
        # https://stackoverflow.com/questions/36479850/python-argparse-check-choices-before-type
        args[LICENSE_POSITIONAL_ARG] = [
            _arg_license_conv(license)
            for license in args[LICENSE_POSITIONAL_ARG]
        ]

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
    github_username = configs[keys.GITHUB_USERNAME_KEY]
    auth = pylib.githubauth.GitHubAuth(configs[keys.GITHUB_API_TOKEN_KEY])
    os.mkdir(_TEMP_DIR)
    os.chdir(_TEMP_DIR)
    repos = [
        repo
        for repo in requests.get(
            GITHUB_USER_REPO_API_URL, auth=auth, params=PAYLOAD
        ).json()
        if not repo["fork"]
    ]

    for license in args[LICENSE_POSITIONAL_ARG]:
        for repo in repos:
            subprocess.run(["git", "clone", repo["html_url"], repo["name"]])
            os.chdir(repo["name"])
            # only expecting to have a single license used throughout the
            # codebase
            if not repo["license"] or license == repo["license"]:
                license_filename = requests.get(
                    os.path.join(
                        GITHUB_REPOS_API_URL,
                        github_username,
                        repo["name"],
                        "license",
                    ),
                    auth=auth,
                ).json()["name"]
                datetime_obj = datetime.datetime.now()
                with open(license_filename, "w") as file:
                    file.write(license.generate_body())
                subprocess.run(["git", "add", f"{license_filename}"])
                subprocess.run(
                    [
                        "git",
                        "commit",
                        "--message",
                        f"Update {license_filename} {datetime_obj.strftime('%d-%b-%Y')}",
                    ]
                )
                subprocess.run(["git", "push"])
            os.chdir("..")
    os.chdir("..")
    shutil.rmtree(_TEMP_DIR)


if __name__ == "__main__":
    args = retrieve_cmd_args()
    main(args)
    sys.exit(0)
