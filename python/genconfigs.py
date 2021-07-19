#!/usr/bin/env python3
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
    
    This command line tool is used to generate the configurations used by the
    scripts in this repo. The configurations are bare and are expected to be
    modified by the end user to take full advantage of using all the scripts.
    The scripts will also use this tool to interface somewhat with the data
    structure that holds the configurations. I say somewhat, as it just
    flattens the data structure on demand to try and curb the amount the other
    scripts need to know about the configuration data structure to use it.

    Attributes
    ----------
    GPS_CONFIG_FILE_PATH : str
        This is the configuration file the program will write/read
        from.
    COMMON_CONFIGURATION_PREFIX : str
        When used as part of script configuration item key. If the rest of
        the string exists as a key at the root of the configuration tree,
        then the program ignores this configuration item. The idea being
        that I wish to track which scripts use which common configuration(s).
    
    """

    # general configurations

    GPS_CONFIG_FILE = "gps.json"
    GPS_CONFIG_FILE_DIR_PATH = appdirs.user_config_dir(PROGRAM_NAME)
    GPS_CONFIG_FILE_PATH = os.path.join(
        GPS_CONFIG_FILE_DIR_PATH, GPS_CONFIG_FILE
    )
    COMMON_CONFIGURATION_PREFIX = "_"  # _FOO

    # configuration keys

    GITHUB_USERNAME_KEY = "github_username"
    GITHUB_API_TOKEN_KEY = "github_api_token"
    SCRIPT_CONFIGS_KEY = "script_configs_keys"
    WEBHOSTED_GIT_ACCOUNT_URL_KEY = "webhosted_git_account_url"
    FORKED_REPOS_TO_UPSTREAM_URLS_KEY = "forked_repos_to_upstream_urls"

    # scripts

    UPDATE_REMOTE_FORKS = "update_remote_forks.py"

    # positional/optional argument labels
    # used at the command line and to reference values of arguments

    EXPORT_SHORT_OPTION = "e"
    EXPORT_LONG_OPTION = "export"
    SHOW_PATH_SHORT_OPTION = "s"
    SHOW_PATH_LONG_OPTION = "show_path"
    SHOW_PATH_CLI_NAME = SHOW_PATH_LONG_OPTION.replace("_", "-")

    # positional/optional argument default values

    EXPORT_OPTION_DEFAULT_VALUE = True

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
        GITHUB_USERNAME_KEY: "",
        GITHUB_API_TOKEN_KEY: "",
        SCRIPT_CONFIGS_KEY: {
            UPDATE_REMOTE_FORKS: {
                WEBHOSTED_GIT_ACCOUNT_URL_KEY: "",
                FORKED_REPOS_TO_UPSTREAM_URLS_KEY: {
                    "awesome-python": "https://github.com/vinta/awesome-python"
                },
            },
        },
    }

    def __init__(self):

        self.json = None

    @classmethod
    def _get_calling_program_name(cls, fil):
        """Determines the calling program's name.

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

        if fil != cls.EXPORT_OPTION_DEFAULT_VALUE:
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
                f"-{cls.EXPORT_SHORT_OPTION}",
                f"--{cls.EXPORT_LONG_OPTION}",
                nargs="?",
                const=cls.EXPORT_OPTION_DEFAULT_VALUE,
                help=(
                    "creates the intermediate configuration file tailored to "
                    "a script"
                ),
                metavar="SCRIPT_NAME",
            )
            cls._arg_parser.add_argument(
                f"-{cls.SHOW_PATH_SHORT_OPTION}",
                f"--{cls.SHOW_PATH_CLI_NAME}",
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
        """Minimizes the depth of the configuration datastructure to three levels.

        Script configurations are added to the root node. Which may at most
        have one more child node. From there, the script configurations tree
        is removed.

        Parameters
        ----------
        script_name : str
            The script name whose configurations are appended to the
            configuration datastructure.

        """

        try:
            script_configs = self.json[self.SCRIPT_CONFIGS_KEY][script_name]
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
        except KeyError as e:
            print(
                f"{PROGRAM_NAME}: "
                f"no known script configurations for {e.args[0]}",
                file=sys.stderr,
            )
            sys.exit(1)

        del self.json[self.SCRIPT_CONFIGS_KEY]

    def _load_json(self):
        """How json files are loaded for the program.

        Returns
        -------
        bool
            If the expected json could not be loaded.

        """
        if not pathlib.Path(self.GPS_CONFIG_FILE_PATH).exists():
            return False
        with open(self.GPS_CONFIG_FILE_PATH, "r") as fil:
            self.json = json.load(fil)
        return True

    def main(self, cmd_args):
        """The main of the program."""
        try:
            if cmd_args[self.SHOW_PATH_LONG_OPTION]:
                print(self.GPS_CONFIG_FILE_PATH)
            elif cmd_args[self.EXPORT_LONG_OPTION]:
                if not self._load_json():
                    raise FileNotFoundError(1, "_", self.GPS_CONFIG_FILE_PATH)
                script_name = self._get_calling_program_name(
                    cmd_args[self.EXPORT_LONG_OPTION]
                )
                self._flatten_genconfigs_configs(script_name)
                print(json.dumps(self.json, indent=4))
            else:
                if not pathlib.Path(self.GPS_CONFIG_FILE_DIR_PATH).exists():
                    os.mkdir(self.GPS_CONFIG_FILE_DIR_PATH)
                with open(self.GPS_CONFIG_FILE_PATH, "w") as fil:
                    json.dump(self.default_genconfigs_configs, fil, indent=4)
            sys.exit(0)
        except FileNotFoundError as e:
            print(
                f"{PROGRAM_NAME}: could not find file: {e.filename}",
                file=sys.stderr,
            )
            sys.exit(1)
        except Exception as e:
            traceback.print_exception(
                type(e), e, e.__traceback__, file=sys.stderr
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
