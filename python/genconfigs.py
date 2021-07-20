#!/usr/bin/env python3
"""Docstring for the genconfigs.py program.

This command line tool is used to generate the configurations used by the
scripts in this repo. The configurations are bare and are expected to be
modified by the end user to take full advantage of using all the scripts.

The scripts will also use this tool to interface somewhat with the
datastructure that holds the configurations. I say somewhat, as it just
flattens the datastructure on demand to try and curb the amount the other
scripts need to know about the configuration datastructure to use it.

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
import pylib

# general program constants

PROGRAM_NAME = os.path.basename(os.path.abspath(__file__))
PROGRAM_ROOT = os.getcwd()


class GenConfigs:
    """Generates/interaces common configurations for scripts in this repo.

    Attributes
    ----------
    GPS_CONFIG_FILE_PATH : str
        This is the configuration file the program will write/read
        from.
    COMMON_CONFIGURATION_PREFIX : str
        When used as part of a script configuration item key. If the rest of
        the string exists as a key at the root of the configuration tree,
        then the program ignores this configuration item. The idea being
        that I wish to track which scripts use which common configuration(s).
    default_genconfigs_configs : dict
        These are the default configurations known to the program and are used
        to generate the program configuration file.

    """

    # general configurations

    _GPS_CONFIG_FILE = "gps.json"
    _GPS_CONFIG_FILE_DIR_PATH = appdirs.user_config_dir(PROGRAM_NAME)
    GPS_CONFIG_FILE_PATH = os.path.join(
        _GPS_CONFIG_FILE_DIR_PATH, _GPS_CONFIG_FILE
    )
    COMMON_CONFIGURATION_PREFIX = "_"  # _FOO

    # configuration keys

    _GITHUB_USERNAME_KEY = "github_username"
    _GITHUB_API_TOKEN_KEY = "github_api_token"
    _SCRIPT_CONFIGS_KEY = "script_configs_keys"
    _WEBHOSTED_GIT_ACCOUNT_URL_KEY = "webhosted_git_account_url"
    _FORKED_REPOS_TO_UPSTREAM_URLS_KEY = "forked_repos_to_upstream_urls"

    # scripts

    _UPDATE_REMOTE_FORKS = "update_remote_forks.py"

    # positional/optional argument labels
    # used at the command line and to reference values of arguments

    _EXPORT_SHORT_OPTION = "e"
    _EXPORT_LONG_OPTION = "export"
    _SHOW_PATH_SHORT_OPTION = "s"
    _SHOW_PATH_LONG_OPTION = "show_path"
    _SHOW_PATH_CLI_NAME = _SHOW_PATH_LONG_OPTION.replace("_", "-")

    # positional/optional argument default values

    _EXPORT_OPTION_DEFAULT_VALUE = True

    _DESC = (
        "Description: Manages common configurations for the scripts in "
        "this repo."
    )
    _arg_parser = argparse.ArgumentParser(
        description=_DESC,
        formatter_class=lambda prog: pylib.argparse.CustomHelpFormatter(
            prog, max_help_position=35
        ),
        allow_abbrev=False,
    )

    default_genconfigs_configs = {
        _GITHUB_USERNAME_KEY: "",
        _GITHUB_API_TOKEN_KEY: "",
        _SCRIPT_CONFIGS_KEY: {
            _UPDATE_REMOTE_FORKS: {
                _WEBHOSTED_GIT_ACCOUNT_URL_KEY: "",
                _FORKED_REPOS_TO_UPSTREAM_URLS_KEY: {
                    "awesome-python": "https://github.com/vinta/awesome-python"
                },
            },
        },
    }

    def __init__(self):

        self.json = None

    @classmethod
    def _get_parent_program_name(cls, fil):
        """Determines the parent program's name.

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

        if fil != cls._EXPORT_OPTION_DEFAULT_VALUE:
            return fil
        else:
            completed_process = subprocess.run(
                [
                    "ps",
                    "--pid",
                    str(os.getppid()),
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

    @classmethod
    def retrieve_cmd_args(cls):
        """How arguments are retrieved from the command line.

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
            cls._arg_parser.add_argument(
                f"-{cls._EXPORT_SHORT_OPTION}",
                f"--{cls._EXPORT_LONG_OPTION}",
                nargs="?",
                const=cls._EXPORT_OPTION_DEFAULT_VALUE,
                help=(
                    "creates the intermediate configuration file tailored to "
                    "a script"
                ),
                metavar="SCRIPT_NAME",
            )
            cls._arg_parser.add_argument(
                f"-{cls._SHOW_PATH_SHORT_OPTION}",
                f"--{cls._SHOW_PATH_CLI_NAME}",
                action="store_true",
                help=(
                    "shows the to-be path for the generated "
                    "configuration file"
                ),
            )

            args = vars(cls._arg_parser.parse_args())
            return args
        except SystemExit:
            sys.exit(1)

    def _flatten_genconfigs_configs(self, script_name):
        """Minimizes the depth of the configuration datastructure loaded.

        Script configurations are added to the root node. Which may at most
        have two child nodes. From there, the script configurations tree
        is removed.

        Parameters
        ----------
        script_name : str
            The script name whose configurations are appended to the
            root of the configuration datastructure.

        """

        # LBYL ok, as currently I except most scripts will just use common
        # configurations, with few using the common configuration prefix.
        script_configs = (
            self.json[self._SCRIPT_CONFIGS_KEY][script_name]
            if script_name in self.json[self._SCRIPT_CONFIGS_KEY]
            else tuple()
        )
        for config in script_configs:
            if (
                self.COMMON_CONFIGURATION_PREFIX in config
                and config[
                    len(
                        self.COMMON_CONFIGURATION_PREFIX
                    ) :  # noqa: E203, black adds padding for complex expressions https://github.com/psf/black/issues/446
                ]
                in self.json
            ):
                continue
            # Surface the key:value pair, in preparation to flatten the
            # data structure.
            self.json[config] = script_configs[config]

        del self.json[self._SCRIPT_CONFIGS_KEY]

    def _load_configs(self):
        """Used to load the instance with the program configuration file.

        Returns
        -------
        bool
            If the config file could be loaded.

        """
        try:
            with open(self.GPS_CONFIG_FILE_PATH, "r") as fil:
                self.json = json.load(fil)
            return True
        except FileNotFoundError:
            return False

    def main(self, cmd_args):
        """The main of the program."""
        try:
            if cmd_args[self._SHOW_PATH_LONG_OPTION]:
                print(self.GPS_CONFIG_FILE_PATH)
            elif cmd_args[self._EXPORT_LONG_OPTION]:
                if not self._load_configs():
                    raise FileNotFoundError(1, "_", self.GPS_CONFIG_FILE_PATH)
                script_name = self._get_parent_program_name(
                    cmd_args[self._EXPORT_LONG_OPTION]
                )
                self._flatten_genconfigs_configs(script_name)
                print(json.dumps(self.json, indent=4))
            else:
                pathlib.Path(self._GPS_CONFIG_FILE_DIR_PATH).mkdir(
                    parents=True, exist_ok=True
                )
                with open(self.GPS_CONFIG_FILE_PATH, "w") as fil:
                    json.dump(self.default_genconfigs_configs, fil, indent=4)
            sys.exit(0)
        except FileNotFoundError as except_obj:
            print(
                f"{PROGRAM_NAME}: could not find file: {except_obj.filename}",
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
                f"{PROGRAM_NAME}: an unknown error occurred, see the above!",
                file=sys.stderr,
            )
            sys.exit(1)
        sys.exit(0)


class GenConfigsRunner:
    """Wrapper class that starts the running of the program."""

    @classmethod
    def main(cls):
        """Entry point in starting the program."""
        genconfig = GenConfigs()
        args = genconfig.retrieve_cmd_args()
        genconfig.main(args)


if __name__ == "__main__":
    GenConfigsRunner.main()
