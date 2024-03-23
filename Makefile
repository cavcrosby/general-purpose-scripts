# special makefile variables
.DEFAULT_GOAL := help
.RECIPEPREFIX := >

# recursively expanded variables
SHELL = /usr/bin/sh

# gnu install directory variables
prefix = ${HOME}/.local
exec_prefix = ${prefix}
includedir = ${prefix}/include
bin_dir = ${exec_prefix}/bin

# targets
HELP = help
SETUP = setup
CLEAN = clean

# executables
GENCONFIGS = genconfigs
PYTHON = python
PIP = pip

# simply expanded variables
executables := \
	${PYTHON}

# inspired from:
# https://stackoverflow.com/questions/5618615/check-if-a-program-exists-from-a-makefile#answer-25668869
_check_executables := $(foreach exec,${executables},$(if $(shell command -v ${exec}),pass,$(error "No ${exec} in PATH")))

.PHONY: ${HELP}
${HELP}:
	# inspired by the makefiles of the Linux kernel and Mercurial
>	@echo 'Common make targets:'
>	@echo '  ${SETUP}              - this runs additional commands in preparation to deploy'
>	@echo '                       scripts on the current machine'
>	@echo '  ${CLEAN}              - removes files generated from other targets'
>	@echo 'Common make configurations (e.g. make [config]=1 [targets]):'
>	@echo '  bin_dir            - determines the where links are installed/uninstalled'
>	@echo '                       from (default: $${HOME}/.local/bin)'

.PHONY: ${SETUP}
${SETUP}:
>	mkdir --parents "${bin_dir}"

	# installs the genconfigs program and initializes it
>	ln --symbolic --force "${CURDIR}/${GENCONFIGS}" "${bin_dir}/${GENCONFIGS}"
>	${CURDIR}/${GENCONFIGS}
>	chmod 600 "$$(${CURDIR}/${GENCONFIGS} --show-path)"
>	${PYTHON} -m ${PIP} install --upgrade "${PIP}"
>	${PYTHON} -m ${PIP} install \
		--requirement "./requirements.txt" \
		--requirement "./requirements-dev.txt"

.PHONY: ${CLEAN}
${CLEAN}:
>	@echo "make: nothing to clean!"
