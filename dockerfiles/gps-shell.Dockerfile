FROM debian:bullseye-slim

ARG BRANCH
ARG COMMIT
LABEL tech.cavcrosby.gps.shell.branch="${BRANCH}"
LABEL tech.cavcrosby.gps.shell.commit="${COMMIT}"
LABEL tech.cavcrosby.gps.shell.vcs-repo="https://github.com/cavcrosby/general-purpose-scripts"

# create user that Jenkins job will run as
ENV RUNNER_USER_NAME="runner"
ENV RUNNER_USER_ID=1000
ENV RUNNER_GROUP_NAME="runner"
ENV RUNNER_GROUP_ID=1000
ENV RUNNER_USER_HOME="/home/runner"

ENV CAVCROSBY_MAKEFILES_GPG_PATH "/usr/share/keyrings/cavcrosby-makefiles-archive-keyring.gpg"
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
    jq

# create a (phony) pyenv shim
RUN touch /usr/bin/pyenv

# ensure bourne shell exists in /usr/bin
RUN ln --symbolic --force /bin/sh /usr/bin/sh
 
# create a make shim
RUN echo "#!/bin/sh"                                                            > "${MAKE_SHIM_PATH}" \
    && echo "#"                                                                 >> "${MAKE_SHIM_PATH}" \
    && echo "#"                                                                 >> "${MAKE_SHIM_PATH}" \
    && echo ""                                                                  >> "${MAKE_SHIM_PATH}" \
    && echo "set -e"                                                            >> "${MAKE_SHIM_PATH}" \
    && echo '. "/etc/profile.d/cavcrosby-makefiles"'                            >> "${MAKE_SHIM_PATH}" \
    && echo ""                                                                  >> "${MAKE_SHIM_PATH}" \
    && echo 'PATH="${PATH}:${HOME}/.local/bin"'                                 >> "${MAKE_SHIM_PATH}" \
    && echo "export PATH"                                                       >> "${MAKE_SHIM_PATH}" \
    && echo ""                                                                  >> "${MAKE_SHIM_PATH}" \
    && echo '/usr/bin/make --include-dir "${CAVCROSBY_MAKEFILES_PATH}" "$@"'    >> "${MAKE_SHIM_PATH}"

RUN chmod +x "${MAKE_SHIM_PATH}"
USER "${RUNNER_USER_NAME}"
WORKDIR "${RUNNER_USER_HOME}"
