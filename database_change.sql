-- Version 2.10


ALTER TABLE trades ADD COLUMN IF NOT EXISTS open_usd_rate varchar(30);
ALTER TABLE trades ADD COLUMN IF NOT EXISTS open_gbp_rate varchar(30);
ALTER TABLE trades ADD COLUMN IF NOT EXISTS close_usd_rate varchar(30);
ALTER TABLE trades COLUMN IF NOT EXISTS ADD close_usd_rate varchar(30);
UPDATE trades SET close_usd_rate = rate;
ALTER TABLE TABLE trades DROP COLUMN rate;

