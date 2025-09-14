# 9.7.8

drop view if exists profit_by_direction;
drop view if exists profit_daily_direction_open;
drop view if exists profit_daily_direction_close;

create view profit_daily_direction_open as
select cast(`profit`.`open_time` as date) AS `day`,sum(`profit`.`net_perc`) AS `net_perc`,count(0) AS `count(*)`,`profit`.`direction` AS `direction`,sum(case when `profit`.`net_perc` > 0 then 1 else 0 end) / count(0) * 100 AS `net_perc_profitable` , sum(`profit`.`net_perc`) / count(0) AS `avg_net_perc`, max(`profit`.`net_perc`) AS `max_net_perc`, min(`profit`.`net_perc`) AS `min_net_perc`  from `greencandle`.`profit` group by cast(`profit`.`open_time` as date),`profit`.`direction` order by cast(`profit`.`open_time` as date) desc;

create view profit_daily_direction_close as
select cast(`profit`.`close_time` as date) AS `day`,sum(`profit`.`net_perc`) AS `net_perc`,count(0) AS `count(*)`,`profit`.`direction` AS `direction`,sum(case when `profit`.`net_perc` > 0 then 1 else 0 end) / count(0) * 100 AS `net_perc_profitable` , sum(`profit`.`net_perc`) / count(0) AS `avg_net_perc`, max(`profit`.`net_perc`) AS `max_net_perc`, min(`profit`.`net_perc`) AS `min_net_perc` from `greencandle`.`profit` group by cast(`profit`.`close_time` as date),`profit`.`direction` order by cast(`profit`.`close_time` as date) desc;

drop view if exists profit_daily_by_close;
drop view if exists profit_daily_by_open;
drop view if exists profit_daily_close;
drop view if exists profit_daily_open;

create view profit_daily_close as
select cast(`profit`.`close_time` as date) AS `date`,dayname(`profit`.`close_time`) AS `day`,sum(cast(`profit`.`net_perc` as decimal(12,2))) AS `sum_net_perc`,avg(cast(`profit`.`net_perc` as decimal(12,2))) AS `avg_net_perc`,max(cast(`profit`.`net_perc` as decimal(12,2))) AS `max_net_perc`,min(cast(`profit`.`net_perc` as decimal(12,2))) AS `min_net_perc`,count(0) AS `count`,sum(case when `profit`.`net_perc` < 0 then 1 else 0 end) AS `net_loss`,sum(case when `profit`.`net_perc` > 0 then 1 else 0 end) / count(0) * 100 AS `perc_profitable`,sum(case when `profit`.`net_perc` > 0 then 1 else 0 end) / count(0) * 100 AS `net_perc_profitable`,sum(cast(`profit`.`usd_net_profit` as decimal(12,2))) AS `usd_net_profit` from `greencandle`.`profit` group by cast(`profit`.`close_time` as date) order by cast(`profit`.`close_time` as date) desc;

create view profit_daily_open as
select cast(`profit`.`open_time` as date) AS `date`,dayname(`profit`.`open_time`) AS `day`,sum(cast(`profit`.`net_perc` as decimal(12,2))) AS `sum_net_perc`,avg(cast(`profit`.`net_perc` as decimal(12,2))) AS `avg_net_perc`,max(cast(`profit`.`net_perc` as decimal(12,2))) AS `max_net_perc`,min(cast(`profit`.`net_perc` as decimal(12,2))) AS `min_net_perc`,count(0) AS `count`,sum(case when `profit`.`net_perc` < 0 then 1 else 0 end) AS `net_loss`,sum(case when `profit`.`net_perc` > 0 then 1 else 0 end) / count(0) * 100 AS `perc_profitable`,sum(case when `profit`.`net_perc` > 0 then 1 else 0 end) / count(0) * 100 AS `net_perc_profitable`,sum(cast(`profit`.`usd_net_profit` as decimal(12,2))) AS `usd_net_profit` from `greencandle`.`profit` group by cast(`profit`.`open_time` as date) order by cast(`profit`.`open_time` as date) desc;

drop view if exists profit_by_dayname_direction;
drop view if exists profit_dayname_direction_open;
drop view if exists profit_dayname_direction_close;

create view profit_dayname_direction_open as
select dayname(`profit`.`open_time`) AS `day_name`,sum(`profit`.`net_perc`) AS `net_perc`,`profit`.`direction` AS `direction`,sum(case when `profit`.`net_perc` > 0 then 1 else 0 end) / count(0) * 100 AS `net_perc_profitable` , sum(`profit`.`net_perc`) / count(0) AS `avg_net_perc`, max(`profit`.`net_perc`) AS `max_net_perc`, min(`profit`.`net_perc`) AS `min_net_perc`  from `greencandle`.`profit` group by dayname(`profit`.`open_time`),`profit`.`direction` order by field(`profit`.`day`,'Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday');


create view profit_dayname_direction_close as
select dayname(`profit`.`close_time`) AS `day_name`,sum(`profit`.`net_perc`) AS `net_perc`,`profit`.`direction` AS `direction`,sum(case when `profit`.`net_perc` > 0 then 1 else 0 end) / count(0) * 100 AS `net_perc_profitable`, sum(`profit`.`net_perc`) / count(0) AS `avg_net_perc`, max(`profit`.`net_perc`) AS `max_net_perc`, min(`profit`.`net_perc`) AS `min_net_perc` from `greencandle`.`profit` group by dayname(`profit`.`close_time`),`profit`.`direction` order by field(`profit`.`day`,'Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday');


drop view if exists profit_by_name_direction;
drop view if exists profitable_by_name_date;
drop view if exists profit_daily_name_open;
drop view if exists profit_daily_name_close;

create view profit_daily_name_open as select `profit`.`name` AS `name`,`profit`.`direction` AS `direction`,cast(`profit`.`open_time` as date) AS `date`,count(0) AS `total`,sum(case when `profit`.`perc` > 0 then 1 else 0 end) AS `profit`,sum(case when `profit`.`net_perc` > 0 then 1 else 0 end) AS `net_profit`,sum(case when `profit`.`net_perc` < 0 then 1 else 0 end) AS `net_loss`,sum(case when `profit`.`perc` > 0 then 1 else 0 end) / count(0) * 100 AS `perc_profitable`,sum(case when `profit`.`net_perc` > 0 then 1 else 0 end) / count(0) * 100 AS `net_perc_profitable`,sum(`profit`.`perc`) AS `total_perc`,sum(`profit`.`perc`) / count(0) AS `per_trade`,sum(`profit`.`net_perc`) AS `total_net_perc`,sum(`profit`.`net_perc`) / count(0) AS `net_per_trade`,max(`profit`.`perc`) AS `max(perc)`,min(`profit`.`perc`) AS `min(perc)`,max(`profit`.`net_perc`) AS `max(net_perc)`,min(`profit`.`net_perc`) AS `min(net_perc)` from `greencandle`.`profit` group by `profit`.`name`,cast(`profit`.`open_time` as date),`profit`.`direction` order by cast(`profit`.`open_time` as date) desc;


create view profit_daily_name_close as select `profit`.`name` AS `name`,`profit`.`direction` AS `direction`,cast(`profit`.`close_time` as date) AS `date`,count(0) AS `total`,sum(case when `profit`.`perc` > 0 then 1 else 0 end) AS `profit`,sum(case when `profit`.`net_perc` > 0 then 1 else 0 end) AS `net_profit`,sum(case when `profit`.`net_perc` < 0 then 1 else 0 end) AS `net_loss`,sum(case when `profit`.`perc` > 0 then 1 else 0 end) / count(0) * 100 AS `perc_profitable`,sum(case when `profit`.`net_perc` > 0 then 1 else 0 end) / count(0) * 100 AS `net_perc_profitable`,sum(`profit`.`perc`) AS `total_perc`,sum(`profit`.`perc`) / count(0) AS `per_trade`,sum(`profit`.`net_perc`) AS `total_net_perc`,sum(`profit`.`net_perc`) / count(0) AS `net_per_trade`,max(`profit`.`perc`) AS `max(perc)`,min(`profit`.`perc`) AS `min(perc)`,max(`profit`.`net_perc`) AS `max(net_perc)`,min(`profit`.`net_perc`) AS `min(net_perc)` from `greencandle`.`profit` group by `profit`.`name`,cast(`profit`.`close_time` as date),`profit`.`direction` order by cast(`profit`.`close_time` as date) desc;


drop view if exists profitable_by_name;
drop view if exists profit_name;
create view profit_name as select `profit`.`name` AS `name`,count(0) AS `total`,sum(case when `profit`.`perc` > 0 then 1 else 0 end) AS `profit`,sum(case when `profit`.`net_perc` > 0 then 1 else 0 end) AS `net_profit`,sum(case when `profit`.`net_perc` < 0 then 1 else 0 end) AS `net_loss`,sum(case when `profit`.`perc` > 0 then 1 else 0 end) / count(0) * 100 AS `perc_profitable`,sum(case when `profit`.`net_perc` > 0 then 1 else 0 end) / count(0) * 100 AS `net_perc_profitable`,sum(`profit`.`perc`) AS `total_perc`,sum(`profit`.`perc`) / count(0) AS `per_trade`,sum(`profit`.`net_perc`) AS `total_net_perc`,sum(`profit`.`net_perc`) / count(0) AS `net_per_trade`,max(`profit`.`perc`) AS `max(perc)`,min(`profit`.`perc`) AS `min(perc)`,max(`profit`.`net_perc`) AS `max(net_perc)`,min(`profit`.`net_perc`) AS `min(net_perc)` from `greencandle`.`profit` group by `profit`.`name` order by sum(case when `profit`.`perc` > 0 then 1 else 0 end) / count(0) * 100 desc;

drop view if exists profit_weekly;
drop view if exists profit_weekly_open;
drop view if exists profit_weekly_close;

create view profit_weekly_open as select concat(year(`profit`.`open_time`),'/',week(`profit`.`open_time`)) AS `week_no`,`FIRST_DAY_OF_WEEK`(cast(`profit`.`open_time` as date)) AS `week_commencing`,count(0) AS `count`,sum(`profit`.`usd_profit`) AS `usd_profit`,sum(`profit`.`usd_net_profit`) AS `usd_net_profit`,sum(`profit`.`perc`) AS `perc`,sum(`profit`.`net_perc`) AS `net_perc` from `greencandle`.`profit` where week(`profit`.`open_time`) is not null group by concat(year(`profit`.`open_time`),'/',week(`profit`.`open_time`)) order by year(`profit`.`open_time`) desc,week(`profit`.`open_time`) desc;

create view profit_weekly_close as select concat(year(`profit`.`close_time`),'/',week(`profit`.`close_time`)) AS `week_no`,`FIRST_DAY_OF_WEEK`(cast(`profit`.`close_time` as date)) AS `week_commencing`,count(0) AS `count`,sum(`profit`.`usd_profit`) AS `usd_profit`,sum(`profit`.`usd_net_profit`) AS `usd_net_profit`,sum(`profit`.`perc`) AS `perc`,sum(`profit`.`net_perc`) AS `net_perc` from `greencandle`.`profit` where week(`profit`.`close_time`) is not null group by concat(year(`profit`.`close_time`),'/',week(`profit`.`close_time`)) order by year(`profit`.`close_time`) desc,week(`profit`.`close_time`) desc;

drop view if exists profit_hourly;
drop view if exists profit_hourly_open;
drop view if exists profit_hourly_close;
drop view if exists profit_by_direction_hour_close;
drop view if exists profit_by_direction_hour_open;
drop view if exists profit_hourly_direction_open;
drop view if exists profit_hourly_direction_close;

create view profit_hourly_direction_open as select cast(`profit`.`open_time` as date) AS `day`,hour(`profit`.`open_time`) AS `hour`,sum(`profit`.`net_perc`) AS `net_perc`,count(0) AS `count`,`profit`.`name` AS `name`,`profit`.`direction` AS `direction`,sum(case when `profit`.`net_perc` > 0 then 1 else 0 end) / count(0) * 100 AS `net_perc_profitable`,sum(`profit`.`net_perc`) / count(0) AS `avg_net_perc`,max(`profit`.`net_perc`) AS `max_net_perc`,min(`profit`.`net_perc`) AS `min_net_perc` from `greencandle`.`profit` group by cast(`profit`.`open_time` as date),`profit`.`direction`,`profit`.`name`,hour(`profit`.`open_time`) order by cast(`profit`.`open_time` as date) desc;

create view profit_hourly_direction_close as select cast(`profit`.`close_time` as date) AS `day`,hour(`profit`.`close_time`) AS `hour`,sum(`profit`.`net_perc`) AS `net_perc`,count(0) AS `count`,`profit`.`name` AS `name`,`profit`.`direction` AS `direction`,sum(case when `profit`.`net_perc` > 0 then 1 else 0 end) / count(0) * 100 AS `net_perc_profitable`,sum(`profit`.`net_perc`) / count(0) AS `avg_net_perc`,max(`profit`.`net_perc`) AS `max_net_perc`,min(`profit`.`net_perc`) AS `min_net_perc` from `greencandle`.`profit` group by cast(`profit`.`close_time` as date),`profit`.`direction`,`profit`.`name`,hour(`profit`.`close_time`) order by cast(`profit`.`close_time` as date) desc;

create view profit_hourly_close as select date_format(`profit`.`close_time`,'%Y-%m-%d') AS `date`,dayname(`profit`.`close_time`) AS `day`,date_format(`profit`.`close_time`,'%H') AS `hour`,sum(`profit`.`perc`) AS `total_perc`,sum(`profit`.`net_perc`) AS `total_net_perc`,avg(`profit`.`perc`) AS `avg_perc`,avg(`profit`.`net_perc`) AS `avg_net_perc`,sum(`profit`.`usd_profit`) AS `usd_profit`,sum(`profit`.`usd_net_profit`) AS `usd_net_profit`,count(0) AS `num_trades` from `greencandle`.`profit` where year(`profit`.`close_time`) <> 0 group by hour(`profit`.`close_time`),dayofmonth(`profit`.`close_time`),month(`profit`.`close_time`),year(`profit`.`close_time`) order by `profit`.`close_time` desc;

create view profit_hourly_open as select date_format(`profit`.`open_time`,'%Y-%m-%d') AS `date`,dayname(`profit`.`open_time`) AS `day`,date_format(`profit`.`open_time`,'%H') AS `hour`,sum(`profit`.`perc`) AS `total_perc`,sum(`profit`.`net_perc`) AS `total_net_perc`,avg(`profit`.`perc`) AS `avg_perc`,avg(`profit`.`net_perc`) AS `avg_net_perc`,sum(`profit`.`usd_profit`) AS `usd_profit`,sum(`profit`.`usd_net_profit`) AS `usd_net_profit`,count(0) AS `num_trades` from `greencandle`.`profit` where year(`profit`.`open_time`) <> 0 group by hour(`profit`.`open_time`),dayofmonth(`profit`.`open_time`),month(`profit`.`open_time`),year(`profit`.`open_time`) order by `profit`.`open_time` desc;

drop view if exists profitable_all;


ALTER TABLE `trades` ADD INDEX IF NOT EXISTS `name_idx` (`name`);
ALTER TABLE `trades` ADD INDEX IF NOT EXISTS `pair_idx` (`pair`);
ALTER TABLE `trades` ADD INDEX IF NOT EXISTS `direction_idx` (`direction`);
ALTER TABLE `trades` ADD INDEX IF NOT EXISTS `close_price_idx` (`close_price`);
