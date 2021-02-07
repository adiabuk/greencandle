-- Version 1.9

use greencandle;
set global max_connections = 2000;

drop view if exists profit;
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`%` SQL SECURITY DEFINER VIEW `profit` AS select `trades`.`open_time` AS `open_time`,`trades`.`interval` AS `interval`,`trades`.`close_time` AS `close_time`,`trades`.`pair` AS `pair`,`trades`.`name` AS `name`,`trades`.`open_price` AS `open_price`,`trades`.`close_price` AS `close_price`,(case when (`trades`.`direction` = 'long') then (((`trades`.`close_price` - `trades`.`open_price`) / `trades`.`open_price`) * 100) else (((`trades`.`base_in` - `trades`.`base_out`) / `trades`.`base_in`) * 100) end) AS `perc`,(case when (`trades`.`direction` = 'long') then (`trades`.`base_out` - `trades`.`base_in`) else (`trades`.`base_in` - `trades`.`base_out`) end) AS `base_profit`,`trades`.`drawdown_perc` AS `drawdown_perc`,`trades`.`drawup_perc` AS `drawup_perc` from `trades`;


drop view if exists daily_profit;
CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`%` SQL SECURITY DEFINER VIEW `daily_profit` AS select left(`profit`.`close_time`,10) AS `date`,sum(`profit`.`perc`) AS `perc` from `profit` where (`profit`.`perc` is not null) group by left(`profit`.`close_time`,10) order by left(`profit`.`close_time`,10),sum(`profit`.`base_profit`);
