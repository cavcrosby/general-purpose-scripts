# special makefile variables
.DEFAULT_GOAL := help
.RECIPEPREFIX := >

# recursive variables
# NOTE: for some reason /bin/sh does not have the 'command' builtin despite
# it being a POSIX requirement, then again one system has /bin as a
# symlink to /usr/bin
SHELL = /usr/bin/sh
python_scripts_dir = ${CURDIR}/python
shell_scripts_dir = ${CURDIR}/shell

# gnu install directory variables
override prefix = ${HOME}/.local
exec_prefix = ${prefix}
# where to add link names that point to repo scripts
bin_dir = ${exec_prefix}/bin

# simply expanded variables
# f ==> file
python_scripts := $(shell find ${python_scripts_dir} -type f)
shell_scripts := $(shell find ${shell_scripts_dir} -type f)

.PHONY: help
help:
	# inspired by the makefiles of the Linux kernel and Mercurial
>	@echo 'Available make targets:'
>	@echo '  install        - links each script in this repo from a local'
>	@echo '                   user accessible location (at least by default).'
>	@echo '  uninstall      - removes links that were inserted by the install target.'
>	@echo 'make configurations (e.g. make [config]=1 [targets]):'
>	@echo '  prefix         - determines what default bin dir is used to'
>	@echo '                   install links (default is "${prefix}").'

# NOTES: .ONESHELL is needed to ensure all the commands below run in
# one shell session. DO NOT quote the *_scripts variables! This seems
# to cause the shell not to want to iterate over the list of scripts.
# This may only cause an issue if any of the scripts contain a space
# or another IFS character.
.ONESHELL:
.PHONY: install
install:
	# shell function used to create link(s) to script(s)
>	@lnsf() { script_name="$$(basename "$$1")"; ln --symbolic --force "$$1" "${bin_dir}/$${script_name}"; }
	# pscript ==> python script
>	for pscript in ${python_scripts}; do \
>		echo lnsf $${pscript}; \
>		lnsf $${pscript}; \
>	done
	# sscript ==> shell script
>	for sscript in ${shell_scripts}; do \
>		echo lnsf $${sscript}; \
>		lnsf $${sscript}; \
>	done

.PHONY: uninstall
uninstall:
	# shell function used to remove link(s) to script(s)
>	@rmf() { script_name="$$(basename "$$1")"; rm --force "${bin_dir}/$${script_name}"; }
	# pscript ==> python script
>	for pscript in ${python_scripts}; do \
>		echo rmf $${pscript}; \
>		rmf $${pscript}; \
>	done
	# sscript ==> shell script
>	for sscript in ${shell_scripts}; do \
>		echo rmf $${sscript}; \
>		rmf $${sscript}; \
>	done
