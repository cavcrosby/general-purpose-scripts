#!/usr/bin/env python3
# Standard Library Imports
import subprocess
import shutil
import sys
import os
import pathlib
from os.path import realpath

# Third Party Imports
import ruamel.yaml
import toml
from ruamel.yaml.scalarstring import FoldedScalarString as folded

# Local Application Imports


PROGRAM_NAME = os.path.basename(sys.path[0])
PROGRAM_ROOT = os.getcwd()
JOBS_YAML_FILEPATH = f"{PROGRAM_ROOT}/jobs.yaml"
JOB_DSL_ROOT_KEY_YAML = "jobs"
JOB_DSL_SCRIPT_KEY_YAML = "script"
JOB_DSL_FILENAME_REGEX = ".*job-dsl.*"
GIT_REPOS_FILENAME = "jobs.toml"
GIT_REPOS = toml.load(GIT_REPOS_FILENAME)["git"]["repo_urls"]
OTHER_PROGRAMS_NEEDED = ["git", "find"]


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


def main():
    """The main of the program."""
    if not have_other_programs():
        sys.exit(1)
    for repo_url in GIT_REPOS:
        repo_name = os.path.basename(repo_url)
        try:
            completed_process = subprocess.run(
                ["git", "clone", "--quiet", repo_url, repo_name],
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
                encoding="utf-8",
                check=True,
            )
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
            if not pathlib.Path(JOBS_YAML_FILEPATH).exists():
                open(JOBS_YAML_FILEPATH, "w").close()
            with open(JOBS_YAML_FILEPATH, "r") as yaml_f:
                data = yaml.load(yaml_f)
            with open(JOBS_YAML_FILEPATH, "w") as yaml_f:
                # NOTE: inspired from:
                # https://stackoverflow.com/questions/35433838/how-to-dump-a-folded-scalar-to-yaml-in-python-using-ruamel
                # fsc == filecontents-str
                job_dsl_fsc = folded(job_dsl_fc)
                # NOTE2: this handles the situation for multiple job-dsls:
                # create the 'JOB_DSL_SCRIPT_KEY_YAML: job_dsl_fsc' then
                # either merge into JOB_DSL_ROOT_KEY_YAML
                # or create the JOB_DSL_ROOT_KEY_YAML entry and append to it
                if data:
                    data[JOB_DSL_ROOT_KEY_YAML].append(
                        dict([(JOB_DSL_SCRIPT_KEY_YAML, job_dsl_fsc)])
                    )
                else:
                    data = dict([(JOB_DSL_SCRIPT_KEY_YAML, job_dsl_fsc)])
                    data = dict([(JOB_DSL_ROOT_KEY_YAML, [data])])
                yaml.dump(data, yaml_f)
        except subprocess.CalledProcessError:
            print(completed_process.stderr.strip())
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
            # NOTE: incase permission issues at some point while iterating
            # over repos, be nice if program can clean up after itself
            #
            # NOTE2: if sys.exit(1) is raised in except, can be carried over
            # into finally, thus allowing a system to exit with the status
            # code passed as argument as this exception is re-raised
            if (
                os.getcwd() == PROGRAM_ROOT
                and pathlib.Path(repo_name).exists()
            ):
                shutil.rmtree(repo_name)
            else:
                os.chdir("..")
                shutil.rmtree(repo_name)


if __name__ == "__main__":
    main()
    sys.exit(0)
