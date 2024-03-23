FROM python:3.9-slim-bullseye

# create user that Jenkins job will run as
ENV RUNNER_USER_NAME="runner"
ENV RUNNER_USER_ID=1000
ENV RUNNER_GROUP_NAME="runner"
ENV RUNNER_GROUP_ID=1000
ENV RUNNER_USER_HOME="/home/runner"

# create runner user
RUN groupadd --gid "${RUNNER_GROUP_ID}" "${RUNNER_GROUP_NAME}" \    
    && useradd \
        --create-home \
        --home-dir "${RUNNER_USER_HOME}" \
        --uid "${RUNNER_USER_ID}" \
        --gid "${RUNNER_GROUP_ID}" \
        --shell /bin/bash \
        "${RUNNER_USER_NAME}"

# install project dependencies
RUN apt-get update && apt-get install --assume-yes \
    git \
    jq

# ensure bourne shell exists in /usr/bin
RUN ln --symbolic --force /bin/sh /usr/bin/sh

# create runner's ssh configs
RUN mkdir --parents "${RUNNER_USER_HOME}/.ssh" \
    && ssh-keyscan -H "github.com" >> "${RUNNER_USER_HOME}/.ssh/known_hosts" \
    && echo "Host github.com"                                                                                           > "${RUNNER_USER_HOME}/.ssh/config" \
    && echo "   HostName github.com"                                                                                    >> "${RUNNER_USER_HOME}/.ssh/config" \
    && echo "   User git"                                                                                               >> "${RUNNER_USER_HOME}/.ssh/config" \
    && echo "   IdentityFile ~/.ssh/id_rsa_github/id_rsa_github"      >> "${RUNNER_USER_HOME}/.ssh/config" \
    && chown --recursive "${RUNNER_USER_NAME}":"${RUNNER_GROUP_NAME}" "${RUNNER_USER_HOME}/.ssh"
 
USER "${RUNNER_USER_NAME}"
WORKDIR "${RUNNER_USER_HOME}"
