FROM python:3.9-slim-bullseye

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

USER "${RUNNER_USER_NAME}"
WORKDIR "${RUNNER_USER_HOME}"
