#!/usr/bin/env python3
# Standard Library Imports
import subprocess
import shutil
import sys
import os
import pathlib
import argparse
from os.path import realpath

# Third Party Imports
import ruamel.yaml
import toml
from ruamel.yaml.scalarstring import FoldedScalarString as folded

# Local Application Imports

# general program configurations

PROGRAM_NAME = os.path.basename(sys.path[0])
PROGRAM_ROOT = os.getcwd()
OTHER_PROGRAMS_NEEDED = ["git", "find", "docker"]

# jenkins configurations as code (CasC) specifics

JOB_DSL_ROOT_KEY_YAML = "jobs"
JOB_DSL_SCRIPT_KEY_YAML = "script"
JOB_DSL_FILENAME_REGEX = ".*job-dsl.*"
CASC_JENKINS_CONFIG_PATH = (
    f"{PROGRAM_ROOT}/casc.yaml"  # os.environ["CASC_JENKINS_CONFIG"]
)
MODIFIED_CASC_JENKINS_CONFIG_PATH = (
    f"{PROGRAM_ROOT}/mod_{os.path.basename(CASC_JENKINS_CONFIG_PATH)}"
)

# git configurations

GIT_CONFIG_FILE = "jobs.toml"
GIT_REPOS = toml.load(GIT_CONFIG_FILE)["git"]["repo_urls"]
GIT_REPOS_DIR_PATH = f"{PROGRAM_ROOT}/git_repos"

# subcommands labels
SUBCOMMAND = "subcommand"
ADDJOBS_SUBCOMMAND = "addjobs"

# positional/optional argument labels
# used at the command line and to reference values of arguments

CONFIG_PATH_SHORT_OPTION = "c"
CONFIG_PATH_LONG_OPTION = "config"


class JenkinsConfigurationAsCode:

    pass


class CustomHelpFormatter(argparse.HelpFormatter):

    def _format_action_invocation(self, action):
        if not action.option_strings:
            default = self._get_default_metavar_for_positional(action)
            (metavar,) = self._metavar_formatter(action, default)(1)
            return metavar

        else:
            parts = []

            # if the Optional doesn't take a value, format is:
            #    -s, --long
            if action.nargs == 0:
                parts.extend(action.option_strings)

            # if the Optional takes a value, formats are:
            #    -s, --long=ARG(S) ==> if both short/long
            #    --long=ARG(S) ==> if just long
            #    -s=ARG(S) ==> if just short
            else:
                default = self._get_default_metavar_for_optional(action)
                args_string = self._format_args(action, default)
                for option_string in action.option_strings:
                    if option_string == action.option_strings[-1]:
                        parts.append(f"{option_string}={args_string}")
                    else:
                        parts.append(option_string)

            return ", ".join(parts)


_DESC = """Description: A small utility to aid in the construction of Jenkins containers."""
_parser = argparse.ArgumentParser(
    description=_DESC,
    allow_abbrev=False,
)
_subparsers = _parser.add_subparsers(
    title=f"{SUBCOMMAND}s",
    metavar=f"{SUBCOMMAND}s [options ...]",
    dest=SUBCOMMAND,
)
_subparsers.required = True


def retrieve_cmd_args():
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
        # addjobs
        # NOTE: max_help_position is increased (default is 24)
        # to allow arguments/options help messages be more indented
        # reference:
        # https://stackoverflow.com/questions/46554084/how-to-reduce-indentation-level-of-argument-help-in-argparse
        addjobs = _subparsers.add_parser(
            ADDJOBS_SUBCOMMAND,
            help=f"will add Jenkins jobs to loaded configuration based on job-dsl file(s) in repo(s)",
            formatter_class=lambda prog: CustomHelpFormatter(
                prog,
                max_help_position=30
            ),
            allow_abbrev=False,
        )
        addjobs.add_argument(
            f"-{CONFIG_PATH_SHORT_OPTION}",
            f"--{CONFIG_PATH_LONG_OPTION}",
            help="overwrite default config",
            metavar="CONFIG_PATH",
        )

        args = vars(_parser.parse_args())
        return args
    except SystemExit:
        sys.exit(1)


def have_other_programs():
    """Checks if certain programs can be found on the PATH.

    Returns
    -------
    bool
        If all the specified programs could be found.

    See Also
    --------
    OTHER_PROGRAMS_NEEDED

    """
    for util in OTHER_PROGRAMS_NEEDED:
        if shutil.which(util) is None:
            print(f"{PROGRAM_NAME}: {util} cannot be found on the PATH!")
            return False

    return True


def fetch_git_repos():
    """Fetches/clones git repos, at least those listed in GIT_REPOS.

    These git repos will be placed into the directory from
    the path ==> GIT_REPOS_DIR_PATH.

    Returns
    -------
    git_repo_names: list of str
        A list of git repo names.

    Raises
    ------
    subprocess.CalledProcessError
        If the git client program has issues when
        running.
    PermissionError
        If the user running the command does not have write
        permissions to GIT_REPOS_DIR_PATH.

    See Also
    --------
    GIT_REPOS
    GIT_REPOS_DIR_PATH

    """
    # so I remember, finally always executes
    # from try-except-else-finally block.
    try:
        os.mkdir(GIT_REPOS_DIR_PATH)
        os.chdir(GIT_REPOS_DIR_PATH)
        for repo_url in GIT_REPOS:
            repo_name = os.path.basename(repo_url)
            completed_process = subprocess.run(
                ["git", "clone", "--quiet", repo_url, repo_name],
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
                encoding="utf-8",
                check=True,
            )
    except subprocess.CalledProcessError:
        print(completed_process.stderr.strip())
        raise
    except PermissionError:
        raise
    else:
        return os.listdir()
    finally:
        os.chdir("..")


def find_job_dsl_file():
    """Locates job-dsl files in the PWD using regex.

    Returns
    -------
    job_dsl_files: list of str
        The job-dsl files found.

    Raises
    ------
    subprocess.CalledProcessError
        Incase the program used to find job-dsl files has an issue.

    See Also
    --------
    JOB_DSL_FILENAME_REGEX

    """
    completed_process = subprocess.run(
        [
            "find",
            ".",
            "-regextype",
            "sed",
            "-maxdepth",
            "1",
            "-regex",
            JOB_DSL_FILENAME_REGEX,
        ],
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE,
        encoding="utf-8",
        check=True,
    )
    # everything but the last index, as it is just ''
    # NOTE: while the func name assumes one file will be returned
    # its possible more than one can be returned
    job_dsl_files = completed_process.stdout.split("\n")[:-1]
    return job_dsl_files


def meets_job_dsl_filereqs(repo_name, job_dsl_files):
    """Checks if the found job-dsl files meet specific requirements.

    Should note this is solely program specific and not
    related to the limitations/restrictions of the plugin itself.

    Returns
    -------
    bool
        If all the job-dsl files meet the program requirements.

    """
    num_of_job_dsls = len(job_dsl_files)
    if num_of_job_dsls == 0:
        print(
            f"{PROGRAM_NAME}: {repo_name} does not have a job-dsl file, skip"
        )
        return False
    elif num_of_job_dsls > 1:
        # there should be no ambiguity in what job-dsl script to run
        # NOTE: this is open to change
        print(
            f"{PROGRAM_NAME}: {repo_name} has more than one job-dsl file, skip!"
        )
        return False
    else:
        return True


def generate_job_yaml(repo_names):
    """"""
    os.chdir(GIT_REPOS_DIR_PATH)
    for repo_name in repo_names:
        try:
            os.chdir(repo_name)
            job_dsl_filenames = find_job_dsl_file()
            if not meets_job_dsl_filereqs(repo_name, job_dsl_filenames):
                os.chdir("..")
                shutil.rmtree(repo_name)
                continue
            job_dsl_filename = job_dsl_filenames[0]

            # read in the job_dsl file, fc == filecontents
            with open(job_dsl_filename, "r") as job_dsl_fh:
                job_dsl_fc = job_dsl_fh.read()
            yaml = ruamel.yaml.YAML()
            yaml.width = 1000
            if not pathlib.Path(MODIFIED_CASC_JENKINS_CONFIG_PATH).exists():
                shutil.copyfile(
                    src=CASC_JENKINS_CONFIG_PATH,
                    dst=MODIFIED_CASC_JENKINS_CONFIG_PATH,
                )
            with open(MODIFIED_CASC_JENKINS_CONFIG_PATH, "r") as yaml_f:
                data = yaml.load(yaml_f)
            # TODO(conner@conneracrosby.tech): Add for ability for 'file' entry to be added vs script' ???
            with open(MODIFIED_CASC_JENKINS_CONFIG_PATH, "w") as yaml_f:
                # NOTE: inspired from:
                # https://stackoverflow.com/questions/35433838/how-to-dump-a-folded-scalar-to-yaml-in-python-using-ruamel
                # fsc == filecontents-str
                job_dsl_fsc = folded(job_dsl_fc)
                # NOTE2: this handles the situation for multiple job-dsls:
                # create the 'JOB_DSL_SCRIPT_KEY_YAML: job_dsl_fsc' then
                # either merge into JOB_DSL_ROOT_KEY_YAML
                # or create the JOB_DSL_ROOT_KEY_YAML entry and append to it
                if JOB_DSL_ROOT_KEY_YAML in data:
                    data[JOB_DSL_ROOT_KEY_YAML].append(
                        dict([(JOB_DSL_SCRIPT_KEY_YAML, job_dsl_fsc)])
                    )
                else:
                    script_entry = dict(
                        [(JOB_DSL_SCRIPT_KEY_YAML, job_dsl_fsc)]
                    )
                    data[JOB_DSL_ROOT_KEY_YAML] = [script_entry]
                yaml.dump(data, yaml_f)
        except PermissionError:
            raise


def main(cmd_args):
    """The main of the program."""
    if not have_other_programs():
        sys.exit(1)
    git_repo_names = fetch_git_repos()
    try:
        if cmd_args[SUBCOMMAND] == ADDJOBS_SUBCOMMAND:
            generate_job_yaml(git_repo_names)
            sys.exit(0)
    except (subprocess.CalledProcessError, SystemExit):
        sys.exit(1)
    except PermissionError as e:
        print(
            f"{PROGRAM_NAME}: a particular file/path was unaccessible, {realpath(e)}"
        )
        sys.exit(1)
    except Exception as e:
        print(f"{PROGRAM_NAME}: an unknown error occurred:")
        print(e)
        sys.exit(1)
    finally:
        if pathlib.Path(GIT_REPOS_DIR_PATH).exists():
            shutil.rmtree(GIT_REPOS_DIR_PATH)


if __name__ == "__main__":
    args = retrieve_cmd_args()
    # main(args)
    print(args)
