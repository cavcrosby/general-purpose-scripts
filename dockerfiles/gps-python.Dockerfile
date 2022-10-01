FROM python:3.9-slim-bullseye

ARG BRANCH
ARG COMMIT
LABEL tech.cavcrosby.gps.python.branch="${BRANCH}"
LABEL tech.cavcrosby.gps.python.commit="${COMMIT}"
LABEL tech.cavcrosby.gps.python.vcs-repo="https://github.com/cavcrosby/general-purpose-scripts"

# create user that Jenkins job will run as
ENV RUNNER_USER_NAME="runner"
ENV RUNNER_USER_ID=1000
ENV RUNNER_GROUP_NAME="runner"
ENV RUNNER_GROUP_ID=1000
ENV RUNNER_USER_HOME="/home/runner"

ENV CAVCROSBY_MAKEFILES_GPG_PATH "/usr/share/keyrings/cavcrosby-makefiles-archive-keyring.gpg"
ENV PYENV_ROOT "${RUNNER_USER_HOME}/.pyenv"
ENV MAKE_SHIM_PATH "/usr/local/bin/make"

# create runner user
RUN groupadd --gid "${RUNNER_GROUP_ID}" "${RUNNER_GROUP_NAME}" \    
    && useradd \
        --create-home \
        --home-dir "${RUNNER_USER_HOME}" \
        --uid "${RUNNER_USER_ID}" \
        --gid "${RUNNER_GROUP_ID}" \
        --shell /bin/bash \
        "${RUNNER_USER_NAME}"

# install pyenv
RUN apt-get update && apt-get install --assume-yes \
    curl \
    git

RUN curl "https://pyenv.run" | bash
RUN chown --recursive "${RUNNER_USER_NAME}":"${RUNNER_GROUP_NAME}" "${PYENV_ROOT}"

# install cavcrosby-makefiles
RUN apt-get update && apt-get install --assume-yes \
    apt-transport-https \
    curl \
    debian-archive-keyring \
    gnupg \
    make

RUN curl \
    --fail \
    --silent \
    --show-error \
    --location "https://packagecloud.io/cavcrosby/makefiles/gpgkey" \
    | gpg --dearmor > "${CAVCROSBY_MAKEFILES_GPG_PATH}"

RUN echo \
    "deb [signed-by=${CAVCROSBY_MAKEFILES_GPG_PATH}] https://packagecloud.io/cavcrosby/makefiles/debian bullseye main" \
    > "/etc/apt/sources.list.d/cavcrosby-makefiles.list"

RUN apt-get update && apt-get install --assume-yes \
    cavcrosby-makefiles

# install project dependencies
RUN apt-get update && apt-get install --assume-yes \
    git \
    jq

# ensure bourne shell exists in /usr/bin
RUN ln --symbolic --force /bin/sh /usr/bin/sh

# TODO(cavcrosby): poetry git dependencies are installed into a directory not
# usually writeable by other users. For now I will enable the directory to be
# "world" writeable until I find a maintainable way to get poetry to install git
# dependencies else where. For an issue disucssion on this topic:
# https://github.com/python-poetry/poetry/issues/2475#issuecomment-1005621857
RUN chmod a+w "/usr/local/src"

# create runner's ssh configs
RUN mkdir --parents "${RUNNER_USER_HOME}/.ssh" \
    && ssh-keyscan -H "github.com" >> "${RUNNER_USER_HOME}/.ssh/known_hosts" \
    && echo "Host github.com"                                                                                           > "${RUNNER_USER_HOME}/.ssh/config" \
    && echo "   HostName github.com"                                                                                    >> "${RUNNER_USER_HOME}/.ssh/config" \
    && echo "   User git"                                                                                               >> "${RUNNER_USER_HOME}/.ssh/config" \
    && echo "   IdentityFile ~/.ssh/id_rsa_github/id_rsa_github"      >> "${RUNNER_USER_HOME}/.ssh/config" \
    && chown --recursive "${RUNNER_USER_NAME}":"${RUNNER_GROUP_NAME}" "${RUNNER_USER_HOME}/.ssh"
 
# create a make shim
#
# MONITOR(cavcrosby): recent heredoc like syntax support for Dockerfiles is
# currently still being worked on for kaniko. Such syntax would be far more
# readable than well, this. For reference on the issue discussing heredoc syntax
# support:
# https://github.com/GoogleContainerTools/kaniko/issues/1713
RUN echo "#!/bin/sh"                                                                            > "${MAKE_SHIM_PATH}" \
    && echo "#"                                                                                 >> "${MAKE_SHIM_PATH}" \
    && echo "#"                                                                                 >> "${MAKE_SHIM_PATH}" \
    && echo ""                                                                                  >> "${MAKE_SHIM_PATH}" \
    && echo "set -e"                                                                            >> "${MAKE_SHIM_PATH}" \
    && echo '. "/etc/profile.d/cavcrosby-makefiles"'                                            >> "${MAKE_SHIM_PATH}" \
    && echo ""                                                                                  >> "${MAKE_SHIM_PATH}" \
    && echo 'PATH="${PYENV_ROOT}/shims:${PYENV_ROOT}/bin:${PATH}:${HOME}/.local/bin"'           >> "${MAKE_SHIM_PATH}" \
    && echo "export PATH"                                                                       >> "${MAKE_SHIM_PATH}" \
    && echo ""                                                                                  >> "${MAKE_SHIM_PATH}" \
    && echo '/usr/bin/make --include-dir "${CAVCROSBY_MAKEFILES_PATH}" "$@"'                    >> "${MAKE_SHIM_PATH}"

RUN chmod +x "${MAKE_SHIM_PATH}"
USER "${RUNNER_USER_NAME}"
WORKDIR "${RUNNER_USER_HOME}"
