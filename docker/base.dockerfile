FROM ubuntu:jammy

ENV NODE_VERSION=16.20.0

# install required packages
RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
    curl \
    software-properties-common \
    gettext \
    git \
    git-lfs \
    psmisc \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3 \
    python3-dev \
    python3-pip \
    python3-sphinx \
    python-is-python3

# add yarn ppa
RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -
RUN echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list

# install nodejs and yarn
RUN apt-get update && \
    curl -sSO https://deb.nodesource.com/node_16.x/pool/main/n/nodejs/nodejs_$NODE_VERSION-1nodesource1_amd64.deb && \
    dpkg -i ./nodejs_$NODE_VERSION-1nodesource1_amd64.deb && \
    rm nodejs_$NODE_VERSION-1nodesource1_amd64.deb && \
    apt-get install yarn

RUN git lfs install

# copy Kolibri source code into image
COPY . /kolibri

# do the time-consuming base install commands
# Note: requirements/build.txt is intentionally not installed here - it is only
# used by build_whl.dockerfile, and its setuptools<41 pin (needed for an old
# pex build quirk) breaks Python 3.9+ metadata builds for other packages.
RUN cd /kolibri \
    && pip3 install --timeout 120 --retries 10 -r requirements/dev.txt \
    && pip3 install --timeout 120 --retries 10 -r requirements/test.txt \
    && yarn install --network-timeout 100000
