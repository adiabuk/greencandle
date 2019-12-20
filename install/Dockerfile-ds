FROM visibilityspots/smashing
LABEL branch=${BRANCH}
LABEL commit=${COMMIT}
LABEL date=${DATE}

RUN rm -rf /smashing/config/* /smashing/dashboards/* /smashing/jobs/* /smashing/assets/* /smashing/widgets/*
ADD dashboard/config /smashing/config
ADD dashboard/dashboards /smashing/dashboards
ADD dashboard/jobs /smashing/jobs
ADD dashboard/assets /smashing/assets
ADD dashboard/widgets /smashing/widgets
ADD dashboard/docker-entrypoint.sh /docker-entrypoint.sh
ADD dashboard/install.sh /install.sh

RUN apt-get update; apt-get install -y netcat; apt-get clean && GEMS=mysql2 /install.sh

ARG BRANCH="master"
ARG COMMIT=""
ARG DATE=""

# Now set it as an env var
ENV COMMIT_SHA=${COMMIT}
ENV VERSION=${BRANCH}
ENV BUILD_DATE=${DATE}

CMD ["/docker-entrypoint.sh"]

