-- Version 2.10


ALTER TABLE trades ADD open_usd_rate varchar(30);
ALTER TABLE trades ADD open_gbp_rate varchar(30);
ALTER TABLE trades ADD close_usd_rate varchar(30);
ALTER TABLE trades ADD close_usd_rate varchar(30);
UPDATE trades SET close_usd_rate = rate;
ALTER TABLE TABLE Trades DROP COLUMN rate;

