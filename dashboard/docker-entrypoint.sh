#!/usr/bin/env bash

while ! nc -z mysql 3306; do
  echo Waiting for mysql;
  sleep 1;
done

while ! nc -z redis 6379; do
  echo Waiting for redis;
  sleep 1;
done

exec smashing start $PORT_ARG
