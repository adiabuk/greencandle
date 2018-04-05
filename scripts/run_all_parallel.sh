#!/usr/bin/env bash

 for i in 15m 5m 3m 1m;do
   echo $i;
   ./test_backend.py -a -i $i 2>&1 | tee ${i}.log &
 done

