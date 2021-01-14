use greencandle;
ALTER TABLE open_trades CHANGE buy_price open_price varchar(30);
ALTER TABLE open_trades CHANGE buy_time open_time varchar(30);


ALTER TABLE trades CHANGE buy_time open_time timestamp NULL DEFAULT '0000-00-00 00:00:00';
ALTER TABLE trades CHANGE sell_time close_time timestamp NULL DEFAULT '0000-00-00 00:00:00';
ALTER TABLE trades CHANGE buy_price open_price varchar(30);
ALTER TABLE trades CHANGE sell_price close_price varchar(30);

DROP VIEW profit;
CREATE VIEW profit as select `trades`.`open_time` AS `open_time`,`trades`.`interval` AS `interval`,`trades`.`close_time` AS `close_time`,`trades`.`pair` AS `pair`,`trades`.`open_price` AS `open_price`,`trades`.`close_price` AS `close_price`,(((`trades`.`close_price` - `trades`.`open_price`) / `trades`.`open_price`) * 100) AS `perc`,(`trades`.`base_out` - `trades`.`base_in`) AS `base_profit`,`trades`.`drawdown_perc` AS `drawdown_perc` from `trades` order by (((`trades`.`close_price` - `trades`.`open_price`) / `trades`.`open_price`) * 100) desc;

DROP VIEW daily_profit;
CREATE VIEW daily_profit as  select left(`profit`.`close_time`,10) AS `date`,`profit`.`interval` AS `interval`,sum(`profit`.`base_profit`) AS `profit`,sum(`profit`.`perc`) AS `perc` from `profit` where (`profit`.`perc` is not null) group by left(`profit`.`close_time`,10) order by left(`profit`.`close_time`,10),sum(`profit`.`base_profit`);
