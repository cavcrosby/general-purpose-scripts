# special makefile variables
.DEFAULT_GOAL := help
.RECIPEPREFIX := >

# recursive variables
SHELL = /usr/bin/sh
python_scripts_dir_path = ${CURDIR}/python
shell_scripts_dir_path = ${CURDIR}/shell
VIRTUALENV_PYTHON_VERSION = 3.9.5

# executables
POETRY = poetry
PIP = pip
PYENV = pyenv
PYTHON = python
GENCONFIGS = genconfigs
executables = \
	${PIP}\
	${PYENV}\
	${PYTHON}

# gnu install directory variables
prefix = ${HOME}/.local
exec_prefix = ${prefix}
# where to add link names that point to repo scripts
bin_dir = ${exec_prefix}/bin

# targets
HELP = help
SETUP = setup
PYTHON_SETUP = python-setup
INSTALL = install
PYTHON_INSTALL = python-install
SHELL_INSTALL = shell-install
UNINSTALL = uninstall
PYTHON_UNINSTALL = python-uninstall
SHELL_UNINSTALL = shell-uninstall
CLEAN = clean

# simply expanded variables
# f ==> file
python_scripts := $(shell find ${python_scripts_dir_path} \( -type f \) -and \( -not -iname *.pyc \) -and \( -not -iname keys.py \))
shell_scripts := $(shell find ${shell_scripts_dir_path} -type f)
python_virtualenv_name := $(shell basename ${CURDIR})

# inspired from:
# https://stackoverflow.com/questions/5618615/check-if-a-program-exists-from-a-makefile#answer-25668869
_check_executables := $(foreach exec,${executables},$(if $(shell command -v ${exec}),pass,$(error "No ${exec} in PATH")))

.PHONY: ${HELP}
${HELP}:
	# inspired by the makefiles of the Linux kernel and Mercurial
>	@echo 'Common make targets:'
>	@echo '  ${SETUP}              - this runs additional commands in preparation to deploy'
>	@echo '                       scripts on the current machine'
>	@echo '  ${PYTHON_SETUP}       - creates and configures the virtualenv to be used'
>	@echo '                       by the project (required before ${INSTALL}), also'
>	@echo '                       useful for development'
>	@echo '  ${INSTALL}            - installs all scripts on the current machine'
>	@echo '  ${PYTHON_INSTALL}     - installs python scripts on the current machine'
>	@echo '  ${SHELL_INSTALL}      - installs shell scripts on the current machine'
>	@echo '  ${UNINSTALL}          - removes scripts that were inserted by the ${INSTALL} target'
>	@echo '  ${PYTHON_UNINSTALL}   - removes shims that were inserted by the ${PYTHON_INSTALL}'
>	@echo '                       target and uninstalls the virtualenv'
>	@echo '  ${SHELL_UNINSTALL}    - removes links that were inserted by the ${SHELL_INSTALL}'
>	@echo '                       target'
>	@echo '  ${CLEAN}              - removes files generated from other targets'
>	@echo 'Common make configurations (e.g. make [config]=1 [targets]):'
>	@echo '  bin_dir                       - determines the where links are installed/uninstalled'
>	@echo '                                  from (default: ${bin_dir})'

.PHONY: ${SETUP}
${SETUP}: ${PYTHON_SETUP}

.PHONY: ${PYTHON_SETUP}
${PYTHON_SETUP}:
>	@${PYENV} versions | grep --quiet '${VIRTUALENV_PYTHON_VERSION}$$' || { echo "make: python \"${VIRTUALENV_PYTHON_VERSION}\" is not installed by pyenv"; exit 1; }
>	${PYENV} virtualenv "${VIRTUALENV_PYTHON_VERSION}" "${python_virtualenv_name}"

	# mainly used to enter the virtualenv when in the repo
>	${PYENV} local "${python_virtualenv_name}"
>	export PYENV_VERSION="${python_virtualenv_name}"

	# to ensure the most current versions of dependencies can be installed
>	${PYTHON} -m ${PIP} install --upgrade ${PIP}
>	${PYTHON} -m ${PIP} install ${POETRY}==1.1.7

	# MONITOR(cavcrosby): temporary workaround due to poetry now breaking on some
	# package installs. For reference:
	# https://stackoverflow.com/questions/69836936/poetry-attributeerror-link-object-has-no-attribute-name#answer-69987715
>	${PYTHON} -m ${PIP} install poetry-core==1.0.4

	# --no-root because we only want to install dependencies. 'pyenv exec' is needed
	# as poetry is installed into a virtualenv bin dir that is not added to the
	# current shell PATH.
>	${PYENV} exec ${POETRY} install --no-root || { echo "${POETRY} failed to install project dependencies"; exit 1; }
>	unset PYENV_VERSION

# .ONESHELL is needed to ensure all the commands below run in one shell session.
# Also, DO NOT quote the *_scripts variables! This seems to cause the shell not
# to want to iterate over the list of scripts. This may only cause an issue if
# any of the scripts contain a space or another IFS character.
.ONESHELL:
.PHONY: ${INSTALL}
${INSTALL}: ${PYTHON_INSTALL} ${SHELL_INSTALL}

.PHONY: ${PYTHON_INSTALL}
${PYTHON_INSTALL}:
>	@for pyscript_path in ${python_scripts}; do \
>		pyscript="$$(basename "$${pyscript_path}")"
>		@echo "cat shim ${bin_dir}/$${pyscript}"
>		cat << _EOF_ > "${bin_dir}/$${pyscript}"
>		#!/bin/bash
>		#
>		# Small shim that calls the program below in the proper python virtualenv.
>		# PYENV_VERSION allows the program to run in the python_virtualenv_name without doing
>		# additional shell setup. pyenv will still process the program name through an
>		# appropriately (same) named shim but this will ultimately still call this shim.
>		export PYENV_VERSION="${python_virtualenv_name}"
>		"$${pyscript_path}" "\$$@"
>		unset PYENV_VERSION
>	
>		_EOF_
>
>		chmod 755 "${bin_dir}/$${pyscript}"
>	done

.PHONY: ${SHELL_INSTALL}
${SHELL_INSTALL}:
>	@for shscript_path in ${shell_scripts}; do \
>		shscript="$$(basename "$${shscript_path}")"; \
>		echo ln --symbolic --force "$${shscript_path}" "${bin_dir}/$${shscript}"; \
>		ln --symbolic --force "$${shscript_path}" "${bin_dir}/$${shscript}"; \
>	done

	# installs the genconfigs program and initializes it
>	echo ln --symbolic --force "${CURDIR}/${GENCONFIGS}" "${bin_dir}/${GENCONFIGS}"; \
>	ln --symbolic --force "${CURDIR}/${GENCONFIGS}" "${bin_dir}/${GENCONFIGS}"; \
>	echo ${CURDIR}/${GENCONFIGS}
>	${CURDIR}/${GENCONFIGS}
>	echo chmod 600 "$$(${CURDIR}/${GENCONFIGS} --show-path)"
>	chmod 600 "$$(${CURDIR}/${GENCONFIGS} --show-path)"

.PHONY: ${UNINSTALL}
${UNINSTALL}: ${PYTHON_UNINSTALL} ${SHELL_UNINSTALL}

.PHONY: ${PYTHON_UNINSTALL}
${PYTHON_UNINSTALL}:
>	@for pyscript_path in ${python_scripts}; do \
>		pyscript="$$(basename "$${pyscript_path}")"; \
>		echo rm --force "$${pyscript_path}" "${bin_dir}/$${pyscript}"; \
>		rm --force "${bin_dir}/$${pyscript}"; \
>	done
>	${PYENV} uninstall --force "${python_virtualenv_name}"

.PHONY: ${SHELL_UNINSTALL}
${SHELL_UNINSTALL}:
>	@for shscript_path in ${shell_scripts}; do \
>		shscript="$$(basename "$${shscript_path}")"; \
>		echo rm --force "$${shscript_path}" "${bin_dir}/$${shscript}"; \
>		rm --force "${bin_dir}/$${shscript}"; \
>	done

.PHONY: ${CLEAN}
${CLEAN}:
>	@echo "Nothing to clean!"
