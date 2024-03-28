# special makefile variables
.DEFAULT_GOAL := help
.RECIPEPREFIX := >

# recursively expanded variables
SHELL = /usr/bin/sh

# targets
HELP = help
SETUP = setup
CLEAN = clean

# executables
PYTHON = python
PIP = pip
YAMLLINT = yamllint
GO = go
ACTIONLINT = actionlint

# simply expanded variables
executables := \
	${PYTHON}\
	${GO}

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

.PHONY: ${SETUP}
${SETUP}:
>	${PYTHON} -m ${PIP} install --upgrade "${PIP}"
>	${PYTHON} -m ${PIP} install \
		--requirement "./requirements.txt" \
		--requirement "./requirements-dev.txt"

>	cd "./internal/tools" \
		&& GOBIN="${CURDIR}/bin" ${GO} install "github.com/rhysd/actionlint/cmd/actionlint"

.PHONY: ${LINT}
${LINT}:
>	${YAMLLINT} --strict "."
>	./bin/${ACTIONLINT}

.PHONY: ${CLEAN}
${CLEAN}:
>	@echo "make: nothing to clean!"
