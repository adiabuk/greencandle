FROM python:3.6.9
LABEL branch=${BRANCH}
LABEL commit=${COMMIT}
LABEL date=${DATE}

ADD . /install
RUN bash /install/install/gc-install.sh && \
    cp install/install/docker-entrypoint.sh / && \
    cp install/install/docker-entrypoint-api.sh / && \
    cp -rv /install/config /opt/config && \
    chmod +x /docker-entrypoint.sh

ARG BRANCH="master"
ARG COMMIT=""
ARG DATE=""

# Now set it as an env var
ENV COMMIT_SHA=${COMMIT}
ENV VERSION=${BRANCH}
ENV BUILD_DATE=${DATE}

CMD ["/docker-entrypoint.sh"]
