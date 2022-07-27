-- Version 3.24

use greencandle;

DROP FUNCTION IF EXISTS REMOVE_PERCENT;
CREATE FUNCTION REMOVE_PERCENT(amount decimal(10,2),perc decimal(10,2))
RETURNS decimal(10,2)
RETURN amount - (amount*perc/100);

drop table if exists accounts;
drop view if exists accounts;
create view accounts as
select `p`.`open_time` AS `open_time`,`t`.`close_time` AS `close_time`,`t`.`open_price` AS `open_price`,`t`.`close_price` AS `close_price`,`p`.`perc` AS `perc`,`t`.`borrowed` AS `borrowed`,`p`.`quote_profit` AS `profit`,`t`.`pair` AS `pair`,case when `t`.`pair` like '%BTC' then 'BTC' when `t`.`pair` like '%BNB' then 'BNB' when `t`.`pair` like '%ETH' then 'ETH' when `t`.`pair` like '%USDT' then 'USDT' end AS `quote_pair`,`t`.`name` AS `name`,`t`.`base_out` AS `quote_out`,`t`.`base_in` AS `quote_in`,`t`.`quote_in` AS `amount` from (`greencandle`.`trades` `t` join `greencandle`.`profit` `p`) where `p`.`id` = `t`.`id` and `t`.`close_price` is not null;

drop table if exists profit;
drop view if exists profit;
create view profit as 
select `greencandle`.`trades`.`id` AS `id`,dayname(`greencandle`.`trades`.`open_time`) AS `day`,`greencandle`.`trades`.`open_time` AS `open_time`,`greencandle`.`trades`.`interval` AS `interval`,`greencandle`.`trades`.`close_time` AS `close_time`,`greencandle`.`trades`.`pair` AS `pair`,`greencandle`.`trades`.`name` AS `name`,`greencandle`.`trades`.`open_price` AS `open_price`,`greencandle`.`trades`.`close_price` AS `close_price`,case when `greencandle`.`trades`.`direction` = 'long' then (`greencandle`.`trades`.`quote_out` - `greencandle`.`trades`.`quote_in`) / `greencandle`.`trades`.`quote_in` * 100 else (`greencandle`.`trades`.`open_price` - `greencandle`.`trades`.`close_price`) / `greencandle`.`trades`.`open_price` * 100 end AS `perc`,case when `greencandle`.`trades`.`direction` = 'long' then `greencandle`.`trades`.`quote_out` - `greencandle`.`trades`.`quote_in` else `greencandle`.`trades`.`quote_in` - `greencandle`.`trades`.`quote_out` end AS `quote_profit`,`greencandle`.`trades`.`drawdown_perc` AS `drawdown_perc`,`greencandle`.`trades`.`drawup_perc` AS `drawup_perc`,case when `greencandle`.`trades`.`direction` = 'long' then (`greencandle`.`trades`.`quote_out` - `greencandle`.`trades`.`quote_in`) * `greencandle`.`trades`.`close_usd_rate` else (`greencandle`.`trades`.`quote_in` - `greencandle`.`trades`.`quote_out`) * `greencandle`.`trades`.`close_usd_rate` end AS `usd_profit` from `greencandle`.`trades`;

drop table if exists profit_daily;
drop view if exists profit_daily;
create table profit_daily as 
select left(`profit`.`close_time`,10) AS `date`,dayname(`profit`.`close_time`) AS `day`,sum(`profit`.`perc`) AS `total_perc`,avg(`profit`.`perc`) AS `avg_perc`,sum(`profit`.`usd_profit`) AS `usd_profit`,count(0) AS `count` from `greencandle`.`profit` where `profit`.`perc` is not null group by left(`profit`.`close_time`,10) order by left(`profit`.`close_time`,10) desc;

drop table if exists profit_daily_by_quote_pair;
drop view if exists profit_daily_by_quote_pair;
create view profit_daily_by_quote_pair as
select case when `profit`.`pair` like '%BTC' then 'BTC' when `profit`.`pair` like '%BNB' then 'BNB' when `profit`.`pair` like '%ETH' then 'ETH' when `profit`.`pair` like '%USDT' then 'USDT' end AS `quote_pair`,left(`profit`.`close_time`,10) AS `date`,dayname(`profit`.`close_time`) AS `day`,sum(`profit`.`perc`) AS `perc`,group_concat(distinct `profit`.`pair` separator ' ') AS `pairs`,count(0) AS `count`,case when `profit`.`pair` like '%BTC' then sum(`profit`.`quote_profit`) * 50730.01000000 when `profit`.`pair` like '%BNB' then sum(`profit`.`quote_profit`) * 606.24000000 when `profit`.`pair` like '%ETH' then sum(`profit`.`quote_profit`) * 4083.72000000 when `profit`.`pair` like '%USDT' then sum(`profit`.`quote_profit`) end AS `usd_profit` from `greencandle`.`profit` where `profit`.`close_time`  not like '%0000-00-00%' group by left(`profit`.`close_time`,10),right(`profit`.`pair`,3) order by `profit`.`close_time` desc;

drop table if exists profit_hourly;
drop view if exists profit_hourly;
create view profit_hourly as 
select date_format(`profit`.`close_time`,'%Y-%m-%d') AS `date`,dayname(`profit`.`close_time`) AS `day`,date_format(`profit`.`close_time`,'%H') AS `hour`,sum(`profit`.`perc`) AS `total_perc`,avg(`profit`.`perc`) AS `avg_perc`,sum(`profit`.`usd_profit`) AS `usd_profit`,count(0) AS `num_trades` from `greencandle`.`profit` where year(`profit`.`close_time`) <> 0 group by hour(`profit`.`close_time`),dayofmonth(`profit`.`close_time`),month(`profit`.`close_time`),year(`profit`.`close_time`) order by `profit`.`close_time` desc;

drop table if exists profit_monthly;
drop view if exists profit_monthly;
create view profit_monthly as 
select left(`profit`.`close_time`,7) AS `date`,sum(`profit`.`usd_profit`) AS `usd_profit`,sum(`profit`.`perc`) AS `perc`,count(0) AS `count(*)` from `greencandle`.`profit` where `profit`.`perc` is not null group by left(`profit`.`close_time`,7) order by left(`profit`.`close_time`,7) desc,sum(`profit`.`quote_profit`);


drop table if exists profit_weekly;
drop view if exists profit_weekly;
create view profit_weekly as 
select concat(year(`profit`.`close_time`),'/',week(`profit`.`close_time`)) AS `week_name`,year(`profit`.`close_time`) AS `YEAR(close_time)`,week(`profit`.`close_time`) AS `WEEK(close_time)`,count(0) AS `COUNT(*)`,left(`profit`.`close_time`,7) AS `date`,sum(`profit`.`usd_profit`) AS `usd_profit`,sum(`profit`.`perc`) AS `perc` from `greencandle`.`profit` where week(`profit`.`close_time`) is not null group by concat(year(`profit`.`close_time`),'/',week(`profit`.`close_time`)) order by year(`profit`.`close_time`) desc,week(`profit`.`close_time`) desc;

drop table if exists profitable_all;
drop view if exists profitable_all;
create view profitable_all as
 select `profit`.`pair` AS `pair`,count(0) AS `total`,sum(case when `profit`.`perc` > 0 then 1 else 0 end) AS `profit`,sum(case when `profit`.`perc` < 0 then 1 else 0 end) AS `loss`,sum(case when `profit`.`perc` > 0 then 1 else 0 end) / count(0) * 100 AS `perc_profitable`,sum(`profit`.`perc`) AS `perc`,sum(`profit`.`perc`) / count(0) AS `per_trade`,max(`profit`.`perc`) AS `max(perc)`,min(`profit`.`perc`) AS `min(perc)` from `greencandle`.`profit` where `profit`.`pair` is not null group by `profit`.`pair` order by sum(case when `profit`.`perc` > 0 then 1 else 0 end) / count(0) * 100 desc;

drop table if exists profitable_by_date;
drop view if exists profitable_by_date;
create view profitable_by_date as
select cast(`profit`.`close_time` as date) AS `date`,dayname(`profit`.`close_time`) AS `day`,count(0) AS `total`,sum(case when `profit`.`perc` > 0 then 1 else 0 end) AS `profit`,sum(case when `profit`.`perc` < 0 then 1 else 0 end) AS `loss`,sum(case when `profit`.`perc` > 0 then 1 else 0 end) / count(0) * 100 AS `perc_profitable`,sum(`profit`.`perc`) AS `perc`,sum(`profit`.`perc`) / count(0) AS `per_trade`,max(`profit`.`perc`) AS `max(perc)`,min(`profit`.`perc`) AS `min(perc)` from `greencandle`.`profit` where `profit`.`pair` is not null and cast(`profit`.`close_time` as date) <> '0000-00-00' group by cast(`profit`.`close_time` as date) order by sum(case when `profit`.`perc` > 0 then 1 else 0 end) / count(0) * 100 desc;

drop table if exists profitable_hours;
drop view if exists profitable_hours;
create view profitable_hours as
select `profit_hourly`.`hour` AS `hour`,sum(`profit_hourly`.`total_perc`) AS `hour_perc`,count(0) AS `total_count`,sum(case when `profit_hourly`.`total_perc` > 0 then 1 else 0 end) AS `num_profit`,sum(case when `profit_hourly`.`total_perc` < 0 then 1 else 0 end) AS `num_loss` from `greencandle`.`profit_hourly` group by `profit_hourly`.`hour`;

drop table if exists profitable_month;
drop view if exists profitable_month;
create view profitable_month as 
select `profit`.`pair` AS `pair`,count(0) AS `total`,sum(case when `profit`.`perc` > 0 then 1 else 0 end) AS `profit`,sum(case when `profit`.`perc` < 0 then 1 else 0 end) AS `loss`,sum(case when `profit`.`perc` > 0 then 1 else 0 end) / count(0) * 100 AS `perc_profitable`,sum(`profit`.`perc`) AS `perc`,sum(`profit`.`perc`) / count(0) AS `per_trade`,max(`profit`.`perc`) AS `max(perc)`,min(`profit`.`perc`) AS `min(perc)` from `greencandle`.`profit` where month(`profit`.`close_time`) = month(curdate()) group by `profit`.`pair` order by sum(case when `profit`.`perc` > 0 then 1 else 0 end) / count(0) * 100 desc;

drop table if exists profitable_today;
drop view if exists profitable_today;
create view profitable_today as 
select `profit`.`pair` AS `pair`,count(0) AS `total`,sum(case when `profit`.`perc` > 0 then 1 else 0 end) AS `profit`,sum(case when `profit`.`perc` < 0 then 1 else 0 end) AS `loss`,sum(case when `profit`.`perc` > 0 then 1 else 0 end) / count(0) * 100 AS `perc_profitable`,sum(`profit`.`perc`) AS `perc`,sum(`profit`.`perc`) / count(0) AS `per_trade`,max(`profit`.`perc`) AS `max(perc)`,min(`profit`.`perc`) AS `min(perc)` from `greencandle`.`profit` where cast(`profit`.`close_time` as date) = cast(curdate() as date) group by `profit`.`pair` order by sum(case when `profit`.`perc` > 0 then 1 else 0 end) / count(0) * 100 desc;

drop table if exists profitable_totals;
drop view if exists profitable_totals;
create view profitable_totals as
select `x`.`table_name` AS `table_name`,`x`.`perc_profitable` AS `perc_profitable`,`x`.`total_perc` AS `total_perc`,`x`.`avg_perc` AS `avg_perc`,`x`.`count` AS `count` from (select 'today' AS `table_name`,avg(`profitable_today`.`perc_profitable`) AS `perc_profitable`,sum(`profitable_today`.`perc`) AS `total_perc`,avg(`profitable_today`.`perc`) AS `avg_perc`,count(0) AS `count` from `greencandle`.`profitable_today` union select 'month' AS `table_name`,avg(`profitable_month`.`perc_profitable`) AS `perc_profitable`,sum(`profitable_month`.`perc`) AS `total_perc`,avg(`profitable_month`.`perc`) AS `avg_perc`,count(0) AS `count` from `greencandle`.`profitable_month` union select 'week' AS `table_name`,avg(`profitable_week`.`perc_profitable`) AS `perc_profitable`,sum(`profitable_week`.`perc`) AS `total_perc`,avg(`profitable_week`.`perc`) AS `avg_perc`,count(0) AS `count` from `greencandle`.`profitable_week` union select 'all' AS `table_name`,avg(`profitable_all`.`perc_profitable`) AS `perc_profitable`,sum(`profitable_all`.`perc`) AS `total_perc`,avg(`profitable_all`.`perc`) AS `avg_perc`,count(0) AS `count` from `greencandle`.`profitable_all`) `x` group by `x`.`table_name`;


drop table if exists profitable_week;
drop view if exists profitable_week;
create view profitable_week as 
select `profit`.`pair` AS `pair`,count(0) AS `total`,sum(case when `profit`.`perc` > 0 then 1 else 0 end) AS `profit`,sum(case when `profit`.`perc` < 0 then 1 else 0 end) AS `loss`,sum(case when `profit`.`perc` > 0 then 1 else 0 end) / count(0) * 100 AS `perc_profitable`,sum(`profit`.`perc`) AS `perc`,sum(`profit`.`perc`) / count(0) AS `per_trade`,max(`profit`.`perc`) AS `max(perc)`,min(`profit`.`perc`) AS `min(perc)` from `greencandle`.`profit` where week(`profit`.`close_time`) = week(curdate()) and year(`profit`.`close_time`) = year(curdate()) group by `profit`.`pair` order by sum(case when `profit`.`perc` > 0 then 1 else 0 end) / count(0) * 100 desc;
