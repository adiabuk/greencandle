for pair in `configstore package get data/5m pairs`; do
  echo $pair;
  open "https://tradingview.com/chart?symbol=BINANCE:${pair}&interval=";
  read;
done
