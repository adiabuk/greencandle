#!/usr/bin/env python
#pylint: disable=ungrouped-imports,wrong-import-position,import-error,wrong-import-order,no-member

"""
Get Status of docker containers from docker socket file and send alerts for erroring containers.
This script requires access to the socket file in /var/run/docker.sock, and config loaded into
namespace so that alerts can be sent
Errors will also be printed to STDOUT.
This script is intended to be run from crontab.
"""
import sys
import json
from greencandle.lib import config
config.create_config()
from greencandle.lib.alerts import send_push_notif, send_slack_message

import requests_unixsocket

def get_docker_status(docker_socket):
    """
    Get docker status from socket file
    """
    session = requests_unixsocket.Session()
    container_list = []
    socket = docker_socket.replace("/", "%2F")
    url = "http+unix://{}/containers/json?all=1".format(socket)
    request = session.get(url)
    assert request.status_code == 200
    for container in json.loads(request.content):
        item = (container["Names"], container["Status"])
        if config.main.base_env in item:
            container_list.append(item)
    return container_list

def main():
    """main_function"""

    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("Send alerts if docker containers are down")
        sys.exit(0)


    issues = []
    docker_socket = "/var/run/docker.sock"
    container_list = get_docker_status(docker_socket)

    for item in container_list:
        name = item[0][0].lstrip('/')
        if any(status in item[1] for status in ["unhealthy", "Exited", "Restarting"]) and \
                "Exited (0)" not in item[1] and "k8s" not in name:
            issues.append(name)

    if issues:
        my_string = ', '.join(issues)
        send_push_notif("Issues with docker containers: {}".format(my_string))
        send_slack_message("alerts", "Issues with docker containers: {}".format(my_string))

if __name__ == '__main__':
    main()
