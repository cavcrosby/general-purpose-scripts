"""Renders all jinja templates in the repository."""
# Standard Library Imports
import jinja2
import os
import pathlib
import sys

# Third Party Imports

# Local Application Imports

# constants and other program configurations
JINJA_SEARCH_PATH = pathlib.PurePath(os.getcwd())

# paths should be relative to JINJA_SEARCH_PATH
JINJA_TPL_PATHS = [
    pathlib.PurePath("./.jenkins/general-purpose-scripts.Jenkinsfile.j2"),
    pathlib.PurePath("./dockerfiles/gps-python.Dockerfile.j2"),
    pathlib.PurePath("./dockerfiles/gps-shell.Dockerfile.j2"),
]

CONFIGS = {
    "common": {
        "runner_user_name": "runner",
        "runner_user_id": "1000",
        "runner_group_name": "runner",
        "runner_group_id": "1000",
        "runner_user_home": "/home/runner",
        "github_ssh_key_local_file": "id_rsa_github",
    },
    "jenkinsfile": {
        "common": {
            "env": {"GPS_CONFIG_FILE_PATH": "/usr/local/etc/gps.json"},
            "volume_mounts": {"gps-configs-secret": "/usr/local/etc"},
        }
    },
}


def main():
    """Start the main program execution."""
    tpl_loader = jinja2.FileSystemLoader(searchpath=JINJA_SEARCH_PATH)
    tpl_env = jinja2.Environment(
        loader=tpl_loader,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    for tpl_path in JINJA_TPL_PATHS:
        tpl = tpl_env.get_template(str(tpl_path))

        with open(os.path.splitext(str(tpl_path))[0], "w") as render_target:
            render_target.write(tpl.render(CONFIGS))


if __name__ == "__main__":
    main()
    sys.exit(0)
