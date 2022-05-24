-- Version 3.6

ALTER TABLE trades ADD COLUMN IF NOT EXISTS comm_open VARCHAR(255);
ALTER TABLE trades ADD COLUMN IF NOT EXISTS comm_close VARCHAR(255);
update trades set borrowed=0 where borrowed='';
update trades set multiplier=0 where multiplier='';


