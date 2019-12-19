FROM mariadb:10.1.24

LABEL branch=${BRANCH}
LABEL commit=${COMMIT}
LABEL date=${DATE}


RUN apt-get update \
   && apt-get install -y cron bash wget nginx-extras netcat vim
RUN [ ! -f /usr/local/bin/configstore ] && \
    wget https://github.com/motns/configstore/releases/download/v2.4.0/configstore-2.4.0-linux-amd64.tar.gz -P /tmp && \
    tar zxvf /tmp/configstore-2.4.0-linux-amd64.tar.gz -C /usr/local/bin && \
    rm -rf /tmp/configstore-2.4.0-linux-amd64.tar.gz
RUN mkdir /opt/output
COPY install/docker-entrypoint-mysql.sh /docker-entrypoint.sh
COPY config /opt/config
RUN chmod +x /docker-entrypoint.sh

ARG BRANCH="master"
ARG COMMIT=""
ARG DATE=""

ENV MYSQL_PASSWORD=password
ENV MYSQL_DATABASE=greencandle

ENV COMMIT_SHA=${COMMIT}
ENV VERSION=${BRANCH}
ENV BUILD_DATE=${DATE}



