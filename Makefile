include base.mk

# recursively expanded variables
python_scripts_dir_path = ${CURDIR}/python
shell_scripts_dir_path = ${CURDIR}/shell

# to be passed in at make runtime
PROGLANG = all

# determines which actions to perform on the selected set of scripts
ifeq (${PROGLANG},python)
	PYTHON_SETUP=1
else ifeq (${PROGLANG},all)
	PYTHON_SETUP=1
endif
ifeq (${PROGLANG},shell)
	SHELL_SETUP=1
else ifeq (${PROGLANG},all)
	SHELL_SETUP=1
endif

ifeq (${PROGLANG},python)
	PYTHON_INSTALL=1
else ifeq (${PROGLANG},all)
	PYTHON_INSTALL=1
endif
ifeq (${PROGLANG},shell)
	SHELL_INSTALL=1
else ifeq (${PROGLANG},all)
	SHELL_INSTALL=1
endif

ifeq (${PROGLANG},python)
	PYTHON_UNINSTALL=1
else ifeq (${PROGLANG},all)
	PYTHON_UNINSTALL=1
endif
ifeq (${PROGLANG},shell)
	SHELL_UNINSTALL=1
else ifeq (${PROGLANG},all)
	SHELL_UNINSTALL=1
endif

# include other generic makefiles
include python.mk
# overrides defaults set by included makefiles
VIRTUALENV_PYTHON_VERSION = 3.9.5
PYTHON_VIRTUALENV_NAME = $(shell basename ${CURDIR})

# executables
GENCONFIGS = genconfigs

# simply expanded variables
python_scripts := $(shell find ${python_scripts_dir_path} \( -type f \) \
	-and \( -not -iname *.pyc \) \
	-and \( -not -iname keys.py \) \
)
shell_scripts := $(shell find ${shell_scripts_dir_path} -type f)
executables := \
	${python_executables}

# inspired from:
# https://stackoverflow.com/questions/5618615/check-if-a-program-exists-from-a-makefile#answer-25668869
_check_executables := $(foreach exec,${executables},$(if $(shell command -v ${exec}),pass,$(error "No ${exec} in PATH")))

.PHONY: ${HELP}
${HELP}:
	# inspired by the makefiles of the Linux kernel and Mercurial
>	@echo 'Common make targets:'
>	@echo '  ${SETUP}              - this runs additional commands in preparation to deploy'
>	@echo '                       scripts on the current machine'
>	@echo '  ${INSTALL}            - installs scripts on the current machine'
>	@echo '  ${UNINSTALL}          - removes scripts that were inserted by the ${INSTALL} target'
>	@echo '  ${CLEAN}              - removes files generated from other targets'
>	@echo 'Common make configurations (e.g. make [config]=1 [targets]):'
>	@echo '  bin_dir            - determines the where links are installed/uninstalled'
>	@echo '                       from (default: $${HOME}/.local/bin)'
>	@echo '  PROGLANG           - determines which set of scripts to perform on'

.PHONY: ${SETUP}
${SETUP}:
>	mkdir --parents "${bin_dir}"

	# installs the genconfigs program and initializes it
>	ln --symbolic --force "${CURDIR}/${GENCONFIGS}" "${bin_dir}/${GENCONFIGS}"
>	${CURDIR}/${GENCONFIGS}
>	chmod 600 "$$(${CURDIR}/${GENCONFIGS} --show-path)"

ifneq ($(findstring ${PYTHON_SETUP},${TRUTHY_VALUES}),)
>	${MAKE} ${PYENV_POETRY_SETUP}
endif

ifneq ($(findstring ${SHELL_SETUP},${TRUTHY_VALUES}),)
>	:
endif

# .ONESHELL is needed to ensure all the commands below run in one shell session.
# Also, DO NOT quote the *_scripts variables! This seems to cause the shell not
# to want to iterate over the list of scripts. This may only cause an issue if
# any of the scripts contain a space or another IFS character.
.ONESHELL:
.PHONY: ${INSTALL}
${INSTALL}:
ifneq ($(findstring ${PYTHON_INSTALL},${TRUTHY_VALUES}),)
>	@for pyscript_path in ${python_scripts}; do \
>		pyscript="$$(basename "$${pyscript_path}")"
>		@echo "cat shim ${bin_dir}/$${pyscript}"
>		cat << _EOF_ > "${bin_dir}/$${pyscript}"
>		#!/bin/bash
>		#
>		# Small shim that calls the program below in the proper python virtualenv.
>		# PYENV_VERSION allows the program to run in the PYTHON_VIRTUALENV_NAME without doing
>		# additional shell setup. pyenv will still process the program name through an
>		# appropriately (same) named shim but this will ultimately still call this shim.
>		
>		set -e
>
>		export PYENV_VERSION="${PYTHON_VIRTUALENV_NAME}"
>		PATH="$${PYENV_ROOT}/plugins/pyenv-virtualenv/shims:$${PYENV_ROOT}/shims:$${PYENV_ROOT}/bin:$${PATH}"
>		export PATH
>		"$${pyscript_path}" "\$$@"
>		unset PYENV_VERSION
>	
>		_EOF_
>
>		chmod 755 "${bin_dir}/$${pyscript}"
>	done
endif

ifneq ($(findstring ${SHELL_INSTALL},${TRUTHY_VALUES}),)
>	@for shscript_path in ${shell_scripts}; do \
>		shscript="$$(basename "$${shscript_path}")"; \
>		echo ln --symbolic --force "$${shscript_path}" "${bin_dir}/$${shscript}"; \
>		ln --symbolic --force "$${shscript_path}" "${bin_dir}/$${shscript}"; \
>	done
endif

.PHONY: ${UNINSTALL}
${UNINSTALL}:
ifneq ($(findstring ${PYTHON_UNINSTALL},${TRUTHY_VALUES}),)
>	@for pyscript_path in ${python_scripts}; do \
>		pyscript="$$(basename "$${pyscript_path}")"; \
>		echo rm --force "$${pyscript_path}" "${bin_dir}/$${pyscript}"; \
>		rm --force "${bin_dir}/$${pyscript}"; \
>	done
>	${PYENV} uninstall --force "${PYTHON_VIRTUALENV_NAME}"
endif

ifneq ($(findstring ${SHELL_UNINSTALL},${TRUTHY_VALUES}),)
>	@for shscript_path in ${shell_scripts}; do \
>		shscript="$$(basename "$${shscript_path}")"; \
>		echo rm --force "$${shscript_path}" "${bin_dir}/$${shscript}"; \
>		rm --force "${bin_dir}/$${shscript}"; \
>	done
endif

.PHONY: ${CLEAN}
${CLEAN}:
>	@echo "make: nothing to clean!"
