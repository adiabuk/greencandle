# 7.12

# fix profit_daily_by_open to use open_time in field
drop view if exists profit_daily_by_open;
create view profit_daily_by_open as
select cast(`profit`.`open_time` as date) AS `date`,dayname(`profit`.`open_time`) AS `day`,sum(cast(`profit`.`net_perc` as decimal(12,2))) AS `sum_net_perc`,avg(cast(`profit`.`net_perc` as decimal(12,2))) AS `avg_net_perc`,max(cast(`profit`.`net_perc` as decimal(12,2))) AS `max_net_perc`,min(cast(`profit`.`net_perc` as decimal(12,2))) AS `min_net_perc`,count(0) AS `count`,sum(case when `profit`.`net_perc` < 0 then 1 else 0 end) AS `net_loss`,sum(case when `profit`.`net_perc` > 0 then 1 else 0 end) / count(0) * 100 AS `perc_profitable`,sum(case when `profit`.`net_perc` > 0 then 1 else 0 end) / count(0) * 100 AS `net_perc_profitable`,sum(cast(`profit`.`usd_net_profit` as decimal(12,2))) AS `usd_net_profit` from `greencandle`.`profit` group by cast(`profit`.`open_time` as date) order by cast(`profit`.`open_time` as date) desc;

