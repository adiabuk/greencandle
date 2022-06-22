-- Version 3.19
ALTER TABLE trades MODIFY COLUMN drawdown_perc varchar(10);
ALTER TABLE trades MODIFY COLUMN drawup_perc varchar(10);
ALTER TABLE trades MODIFY drawup_perc varchar(10) AFTER drawdown_perc;

