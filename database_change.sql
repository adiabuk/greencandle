-- Version 2.13

UPDATE trades
   SET base_in=(@temp:=base_in), base_in = quote_in, quote_in = @temp

UPDATE trades
   SET base_out=(@temp:=base_out), base_out = quote_out, quote_out = @temp
