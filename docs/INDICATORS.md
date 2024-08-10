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

## Heiken Ashi
VERIFIED to be equal to tradingview
get_ha;HA;0
always need the last 0 despite not being used, for consistency with other indicators
Usage:
res[0].HA_open > res[0].HA_close # red candle
res[0].HA_open < res[0].HA_close # green candle

## MACD
VERIFIED to be equal to tradingview
Usage: get_macd;MACD;<fast_length>,<slow_lengeth>,<signal_smoothing>
eg: get_macd;MACD;12,26,9

Redis output: (macd, signal, histogram) tupple

## ATR

## ATR PERC
Not yet verified
usage: get_atr_perc;ATRp;<ATR length><Period lookback>
Returns: int percentage


## bbperc
VERIFIED to be equal to tradingview
get_bbperc;name;<period>,<std dev>

eg; get_bb_perc;bbperc;200,1
Usage: res[0].bbperc_200

## Stochrsi
VERIFIED to be equal to tradingview
get_stochrsi;STOCHRSI;8,5,3
<RSI length>,<STOCH length>,<k/d SMOOTH>
Usage: res[0].STOCHRSI_8[0] #for k
Usage: res[0].STOCHRSI_8[1] #for d

Redis output: (k,d) tupple

## Supertrend
VERIFIED to be equal to tradingview
get_super_trend_STX;<ATR Period>,<ATR Multiplier>
get_supertrend;STX;23,3
Output: tupple (direction, value)
direction: -1 (downtrend)
            1 (uptrend)
Usage:
res[0].STX_23[0] > 0
res[0].close > res[0].STX_23[1]

## Moving averages
VERIFIED to be equal to tradingview
get_moving_averages;EMA;8
<function>;<MA><timeframe>
Usage: res[0].EMA_8[0]
Redis output: EMA value, float

<MA> can be MA|SMA|EMA|WMA

## RSI
VERIFIED to be equal to tradingview
get_RSI;RSI;14
<function>;<string><RSI length>
Usage: res[0].RSI_14[0]
Redis output: RSI value, float

## TSI
VERIFIED to be equal to tradingview
get_cci;CCI;100
<function>;<string><CCI length>
Usage: res[0].CCI_199

Redis output: RSI value, float

## pivot
to be verified

## TSI
to be verified

## envelope


## Oscillators (stochf etc)

## Indicators (hammer/doji etc)
