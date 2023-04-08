#!/usr/bin/env bash

declare -A TF2MIN

TF2MIN[1h]="60"
TF2MIN[4h]="240"
TF2MIN[12h]="720"
TF2MIN[1m]="1"
TF2MIN[5m]="5"
TF2MIN[15m]="15"
TF2MIN[30m]="30"

TF=$1
MIN=${TF2MIN[$TF]}

for pair in `configstore package get data/$TF pairs`; do
  echo $pair;
  open "https://tradingview.com/chart?symbol=BINANCE:${pair}&interval=$MIN";
  read;
done
