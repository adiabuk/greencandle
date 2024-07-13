# 7.12

# more digits for drawdown/drawup perc required for upper timeframes

ALTER TABLE trades MODIFY drawup_perc varchar(6);
ALTER TABLE trades MODIFY drawdown_perc varchar(6);
