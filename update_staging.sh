#!/usr/bin/env bash

set -e

git pull
docker-compose -f ./install/docker-compose.yml pull
TAG=$(python greencandle/version.py) docker-compose -f ./install/docker-compose.yml up -d 
