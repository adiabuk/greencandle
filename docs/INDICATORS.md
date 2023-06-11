# Indicators

## Bolilinger bands
get_bb;<period>;<std_dev>
get_bb;12;2
output: [upper, middle, lower]

current lower for period 200:
res[0].bb_200[2]

last middle for period 12:
res[1].bb_12[0]

## Supertrend

## bbperc bbperc_ema

## pivot

## TSI

## RSI

## Stochrsi
get_stochrsi;STOCHRSI;8,5,3
<RSI length>,<STOCH length>,<k/d SMOOTH>

## envelope

## Moving averages

## Oscillators (stochf etc)

## Indicators (hammer/doji etc)
