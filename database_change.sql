-- Version 2.14

UPDATE trades
   SET base_in=(@temp:=base_in), base_in = quote_in, quote_in = @temp;

UPDATE trades
   SET base_out=(@temp:=base_out), base_out = quote_out, quote_out = @temp;


UPDATE trades_16.01.21
   SET base_in=(@temp:=base_in), base_in = quote_in, quote_in = @temp;

UPDATE trades_16.01.21
   SET base_out=(@temp:=base_out), base_out = quote_out, quote_out = @temp;

DROP view profit;
CREATE VIEW `profit` AS select `trades`.`id` AS `id`,`trades`.`open_time` AS `open_time`,`trades`.`interval` AS `interval`,`trades`.`close_time` AS `close_time`, `trades`.`pair` AS `pair`,`trades`.`name` AS `name`,`trades`.`open_price` AS `open_price`,`trades`.`close_price` AS `close_price`,(case when (`trades`.`direction` = 'long') then (((`trades`.`quote_out` - `trades`.`quote_in`) / `trades`.`quote_in`) * 100) else (((`trades`.`open_price` - `trades`.`close_price`) / `trades`.`open_price`) * 100) end) AS `perc`,(case when (`trades`.`direction` = 'long') then (`trades`.`quote_out` - `trades`.`quote_in`) else (`trades`.`quote_in` - `trades`.`quote_out`) end) AS `quote_profit`,`trades`.`drawdown_perc` AS `drawdown_perc`,`trades`.`drawup_perc` AS `drawup_perc`,((`trades`.`quote_out` - `trades`.`quote_in`) * `trades`.`close_usd_rate`) AS `usd_profit` from `trades`;


DROP VIEW accounts;
CREATE VIEW `accounts` AS select `p`.`open_time` AS `open_time`,`t`.`close_time` AS `close_time`,`t`.`open_price` AS `open_price`,`t`.`close_price` AS `close_price`,`p`.`perc` AS `perc`,`t`.`borrowed` AS `borrowed`,`p`.`quote_profit` AS `profit`,`t`.`pair` AS `pair`,(case when (`t`.`pair` like '%BTC') then 'BTC' when (`t`.`pair` like '%BNB') then 'BNB' when (`t`.`pair` like '%ETH') then 'ETH' when (`t`.`pair` like '%USDT') then 'USDT' end) AS `quote_pair`,`t`.`name` AS `name`,`t`.`base_out` AS `quote_out`,`t`.`base_in` AS `quote_in`,`t`.`quote_in` AS `amount` from (`trades` `t` join `profit` `p`) where ((`p`.`id` = `t`.`id`) and (`t`.`close_price` is not null)) ;

DROP VIEW daily_profit_by_base_pair;
CREATE VIEW `daily_profit_by_base_pair` AS select (case when (`profit`.`pair` like '%BTC') then 'BTC' when (`profit`.`pair` like '%BNB') then 'BNB' when (`profit`.`pair` like '%ETH') then 'ETH' when (`profit`.`pair` like '%USDT') then 'USDT' end) AS `base_pair`,left(`profit`.`close_time`,10) AS `date`,sum(`profit`.`perc`) AS `perc`,group_concat(distinct `profit`.`pair` separator ' ') AS `pairs`,count(0) AS `count`,(case when (`profit`.`pair` like '%BTC') then (sum(`profit`.`quote_profit`) * 50730.01000000) when (`profit`.`pair` like '%BNB') then (sum(`profit`.`quote_profit`) * 606.24000000) when (`profit`.`pair` like '%ETH') then (sum(`profit`.`quote_profit`) * 4083.72000000) when (`profit`.`pair` like '%USDT') then sum(`profit`.`quote_profit`) end) AS `usd_profit` from `profit` where (not((`profit`.`close_time` like '%0000-00-00%'))) group by left(`profit`.`close_time`,10),right(`profit`.`pair`,3) order by `profit`.`close_time` desc;

DROP VIEW monthly_profit;
CREATE VIEW `monthly_profit` AS select left(`profit`.`close_time`,7) AS `date`,`profit`.`interval` AS `interval`,sum(`profit`.`quote_profit`) AS `profit`,sum(`profit`.`perc`) AS `perc` from `profit` where (`profit`.`perc` is not null) group by left(`profit`.`close_time`,7) order by left(`profit`.`close_time`,7),sum(`profit`.`quote_profit`);

DROP VIEW daily_profit;
CREATE VIEW `daily_profit` AS select left(`profit`.`close_time`,10) AS `date`,sum(`profit`.`perc`) AS `perc`,sum(`profit`.`usd_profit`) AS `usd_profit` from `profit` where (`profit`.`perc` is not null) group by left(`profit`.`close_time`,10) order by left(`profit`.`close_time`,10),sum(`profit`.`quote_profit`);
