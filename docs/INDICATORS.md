# Indicators

## Bolilinger bands
VERIFIED to be equal to tradingview
get_bb;<name><period>,<std_dev>
get_bb;bb;12,2
Redis output: [upper, middle, lower]

current lower for period 200:
res[0].bb_200[2]

last middle for period 12:
res[1].bb_12[0]
Redis output: (u, m, l) tupple


## bbperc bbperc_ema
VERIFIED to be equal to tradingview
get_bbperc;name;<period>,<std dev>

eg; get_bbperc;bbperc;200,1
Usage: res[0].bbperc_200

## Stochrsi
VERIFIED to be equal to tradingview
get_stochrsi;STOCHRSI;8,5,3
<RSI length>,<STOCH length>,<k/d SMOOTH>
Usage: res[0].STOCHRSI_8[0] #for k
Usage: res[0].STOCHRSI_8[1] #for d

Redis output: (k,d) tupple

## Supertrend
to be verified

## pivot
to be verified

## TSI
to be verified

## RSI
to be verified

## envelope

## Moving averages

## Oscillators (stochf etc)

## Indicators (hammer/doji etc)
