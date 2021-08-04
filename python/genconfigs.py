#!/usr/bin/env python3
"""Generates/interaces common configurations for scripts in the below repo.

This command line tool is used to generate the configurations used by the
scripts in the general-purpose-scripts repo. The configurations are bare and
are expected to be modified by the end user to take full advantage of using
all the scripts.

"""
# Standard Library Imports
import appdirs
import argparse
import json
import os
import pathlib
import subprocess
import sys
import traceback

# Third Party Imports

# Local Application Imports
from pylib.argparse import CustomRawDescriptionHelpFormatter

# constants and other program configurations
_PROGRAM_NAME = os.path.basename(os.path.abspath(__file__))
_arg_parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=lambda prog: CustomRawDescriptionHelpFormatter(
        prog, max_help_position=35
    ),
    allow_abbrev=False,
)

GPS_CONFIG_FILE = "gps.json"
GPS_CONFIG_FILE_DIR_PATH = appdirs.user_config_dir(_PROGRAM_NAME)
GPS_CONFIG_FILE_PATH = os.path.join(GPS_CONFIG_FILE_DIR_PATH, GPS_CONFIG_FILE)
COMMON_CONFIGURATION_PREFIX = "_"  # _FOO

# configuration keys

GITHUB_USERNAME_KEY = "github_username"
GITHUB_API_TOKEN_KEY = "github_api_token"
SCRIPT_CONFIGS_KEY = "script_configs_keys"
WEBHOSTED_GIT_ACCOUNT_URL_KEY = "webhosted_git_account_url"
FORKED_REPOS_TO_UPSTREAM_URLS_KEY = "forked_repos_to_upstream_urls"
OWNER_KEY = "owner"

# scripts

DISABLE_GITHUB_ACTIONS = "disable_github_actions.py"
UPDATE_REMOTE_FORKS = "update_remote_forks.py"

# positional/optional argument labels
# used at the command line and to reference values of arguments

EXPORT_SHORT_OPTION = "e"
EXPORT_LONG_OPTION = "export"
SHOW_PATH_SHORT_OPTION = "s"
SHOW_PATH_LONG_OPTION = "show_path"
SHOW_PATH_CLI_NAME = SHOW_PATH_LONG_OPTION.replace("_", "-")

# positional/optional argument default values

_EXPORT_OPTION_DEFAULT_VALUE = True

DEFAULT_GENCONFIGS_CONFIGS = {
    GITHUB_USERNAME_KEY: "",
    GITHUB_API_TOKEN_KEY: "",
    SCRIPT_CONFIGS_KEY: {
        UPDATE_REMOTE_FORKS: {
            WEBHOSTED_GIT_ACCOUNT_URL_KEY: "",
            FORKED_REPOS_TO_UPSTREAM_URLS_KEY: {
                "awesome-python": "https://github.com/vinta/awesome-python"
            },
        },
        DISABLE_GITHUB_ACTIONS: {OWNER_KEY: ""},
    },
}


def _get_grandparents_pid():
    """Return the grandparent's process id.
    
    Returns
    -------
    str
        The grandparent's process id.
    
    """
    return subprocess.run(
        ["ps", "--pid", str(os.getppid()), "-o", "ppid", "--no-headers"],
        capture_output=True,
        encoding="utf-8",
    ).stdout.strip()


def _get_parent_program_name(fil):
    """Determine the parent program's name.

    Parameters
    ----------
    fil : str
        File/program name that is the parent. Intended for backwards
        compatibility with non-supported operating systems.

    Returns
    -------
    str
        File/program name that is the parent.

    """
    mappings = {"python": 1, "python3": 1}

    if fil != _EXPORT_OPTION_DEFAULT_VALUE:
        return fil
    else:
        # Grandparent's pid is needed because of the shims that are
        # called prior to the actual script.
        completed_process = subprocess.run(
            [
                "ps",
                "--pid",
                str(_get_grandparents_pid()),
                "-o",
                "command",
                "--no-headers",
            ],
            capture_output=True,
            encoding="utf-8",
        )
        process_cmd = completed_process.stdout.strip().split()
        fil_index = mappings.get(
            os.path.basename(process_cmd[0]),
            0,
        )
        return os.path.basename(process_cmd[fil_index])


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
            f"-{EXPORT_SHORT_OPTION}",
            f"--{EXPORT_LONG_OPTION}",
            nargs="?",
            const=_EXPORT_OPTION_DEFAULT_VALUE,
            help=(
                "creates the intermediate configuration file tailored to "
                "a script"
            ),
            metavar="SCRIPT_NAME",
        )
        _arg_parser.add_argument(
            f"-{SHOW_PATH_SHORT_OPTION}",
            f"--{SHOW_PATH_CLI_NAME}",
            action="store_true",
            help=(
                "shows the to-be path for the generated " "configuration file"
            ),
        )

        args = vars(_arg_parser.parse_args())
        return args
    except SystemExit:
        sys.exit(1)


def _flatten_genconfigs_configs(script_name, config_datastructure):
    """Minimize the depth of the configuration datastructure passed in.

    Script configurations are added to the root node. Which may at most
    have two child nodes. From there, the script configurations tree
    is removed.

    Parameters
    ----------
    script_name : str
        The script name whose configurations are appended to the
        root of the configuration datastructure.
    config_datastructure : dict
        The program configuration file contents.

    """
    # LBYL ok, as currently I except most scripts will just use common
    # configurations, with few using the common configuration prefix.
    script_configs = (
        config_datastructure[SCRIPT_CONFIGS_KEY][script_name]
        if script_name in config_datastructure[SCRIPT_CONFIGS_KEY]
        else tuple()
    )
    for config in script_configs:
        if (
            COMMON_CONFIGURATION_PREFIX in config
            and config[  # noqa: W503
                len(
                    COMMON_CONFIGURATION_PREFIX
                ) :  # noqa: E203,E501 black adds padding for complex slice expressions https://github.com/psf/black/issues/446
            ]
            in config_datastructure
        ):
            continue
        # Surface the key:value pair, in preparation to flatten the
        # data structure.
        config_datastructure[config] = script_configs[config]

    del config_datastructure[SCRIPT_CONFIGS_KEY]


def _load_configs():
    """Load the program configuration file.

    Returns
    -------
    dict
        The program configuration file contents.
    bool
        If the config file could be loaded.

    """
    try:
        with open(GPS_CONFIG_FILE_PATH, "r") as fil:
            return json.load(fil)
    except FileNotFoundError:
        return False


def main(args):
    """Start the main program execution."""
    try:
        if args[SHOW_PATH_LONG_OPTION]:
            print(GPS_CONFIG_FILE_PATH)
        elif args[EXPORT_LONG_OPTION]:
            configs = _load_configs()
            if not configs:
                raise FileNotFoundError(1, "_", GPS_CONFIG_FILE_PATH)
            script_name = _get_parent_program_name(args[EXPORT_LONG_OPTION])
            _flatten_genconfigs_configs(script_name, configs)
            print(json.dumps(configs, indent=4))
        else:
            pathlib.Path(GPS_CONFIG_FILE_DIR_PATH).mkdir(
                parents=True, exist_ok=True
            )
            with open(GPS_CONFIG_FILE_PATH, "w") as fil:
                json.dump(DEFAULT_GENCONFIGS_CONFIGS, fil, indent=4)
        sys.exit(0)
    except FileNotFoundError as except_obj:
        print(
            f"{_PROGRAM_NAME}: could not find file: {except_obj.filename}",
            file=sys.stderr,
        )
        sys.exit(1)
    except Exception as except_obj:
        traceback.print_exception(
            type(except_obj),
            except_obj,
            except_obj.__traceback__,
            file=sys.stderr,
        )
        print(
            f"{_PROGRAM_NAME}: an unknown error occurred, see the above!",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    args = retrieve_cmd_args()
    main(args)
    sys.exit(0)
