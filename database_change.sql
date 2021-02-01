use greencandle;

CREATE TABLE if not exists `balance_summary` (
  `ctime` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `usd` double DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

drop view if exists profit;
create VIEW `profit` AS select `trades`.`open_time` AS `open_time`,`trades`.`interval` AS `interval`,`trades`.`close_time` AS `close_time`,`trades`.`pair` AS `pair`, `trades`.`name` AS `name`,`trades`.`open_price` AS `open_price`,`trades`.`close_price` AS `close_price`,(case when (`trades`.`direction` = 'long') then (((`trades`.`close_price` - `trades`.`open_price`) / `trades`.`open_price`) * 100) else (((`trades`.`open_price` - `trades`.`close_price`) / `trades`.`open_price`) * 100) end) AS `perc`,(case when (`trades`.`direction` = 'long') then (`trades`.`base_out` - `trades`.`base_in`) else (`trades`.`base_in` - `trades`.`base_out`) end) AS `base_profit`,`trades`.`drawdown_perc` AS `drawdown_perc`,`trades`.`drawup_perc` AS `drawup_perc` from `trades`;
