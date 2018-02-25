#!/usr/bin/env bash

countdown ()
{
    seconds="$1";
    date1=$(($(date +%s) + seconds -1));
    while [ "$date1" -ge "$(date +%s)" ]; do
        echo -ne "$(date -u --date @$(("$date1" - $(date +%s) )) +%H:%M:%S)\r";
    done
}


while true; do
  ( ./backend.py ) & countdown 300 ; kill $!

done
