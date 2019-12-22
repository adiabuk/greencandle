FROM nginx:stable

LABEL branch=${BRANCH}
LABEL commit=${COMMIT}
LABEL date=${DATE}
LABEL host=${HOST}

RUN apt-get update \
   && apt-get install -y cron bash wget nginx-extras netcat vim && \
   apt-get purge -y guile-2.2-libs libpython2.7-minimal exim4-daemon-light && \
   apt-get -y clean && apt-get -y autoclean && apt-get -y autoremove
RUN [ ! -f /usr/local/bin/configstore ] && \
    wget https://github.com/motns/configstore/releases/download/v2.4.0/configstore-2.4.0-linux-amd64.tar.gz -P /tmp && \
    tar zxvf /tmp/configstore-2.4.0-linux-amd64.tar.gz -C /usr/local/bin && \
    rm -rf /tmp/configstore-2.4.0-linux-amd64.tar.gz
RUN mkdir /opt/output
COPY install/docker-entrypoint.sh /
COPY config /opt/config
RUN chmod +x /docker-entrypoint.sh

ENV COMMIT_SHA=${COMMIT}
ENV VERSION=${BRANCH}
ENV BUILD_DATE=${DATE}

CMD ['/docker-entrypoint.sh nginx -g 'daemon off;']
