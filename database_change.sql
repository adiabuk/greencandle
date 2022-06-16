-- Version 3.16

ALTER TABLE trades ADD COLUMN  borrowed_usd varchar(30) after borrowed;
UPDATE trades SET borrowed_usd=0;
