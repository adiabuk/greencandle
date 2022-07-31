-- Version 3.27

drop view if exists profitable_all;

create view profitable_all as
select `profit`.`pair` AS `pair`, name as name, count(0) AS `total`,sum(case when `profit`.`perc` > 0 then 1 else 0 end) AS `profit`,sum(case when `profit`.`net_perc` > 0 then 1 else 0 end) AS `net_profit`,sum(case when `profit`.`perc` < 0 then 1 else 0 end) AS `loss`,sum(case when `profit`.`net_perc` < 0 then 1 else 0 end) AS `net_loss`,sum(case when `profit`.`perc` > 0 then 1 else 0 end) / count(0) * 100 AS `perc_profitable`,sum(case when `profit`.`net_perc` > 0 then 1 else 0 end) / count(0) * 100 AS `net_perc_profitable`,sum(`profit`.`perc`) AS `perc`,sum(`profit`.`perc`) / count(0) AS `per_trade`,sum(`profit`.`net_perc`) AS `net_perc`,sum(`profit`.`net_perc`) / count(0) AS `net_per_trade`,max(`profit`.`perc`) AS `max(perc)`,min(`profit`.`perc`) AS `min(perc)`,max(`profit`.`net_perc`) AS `max(net_perc)`,min(`profit`.`net_perc`) AS `min(net_perc)` from `greencandle`.`profit` where `profit`.`pair` is not null group by `profit`.`pair`, name order by sum(case when `profit`.`perc` > 0 then 1 else 0 end) / count(0) * 100 desc;


drop view if exists profit_daily;
drop table if exists profit_daily;
create view profit_daily as
select left(`profit`.`close_time`,10) AS `date`,dayname(`profit`.`close_time`) AS `day`,sum(`profit`.`perc`) AS `total_perc`,sum(`profit`.`net_perc`) AS `total_net_perc`,avg(`profit`.`perc`) AS `avg_perc`,avg(`profit`.`net_perc`) AS `avg_net_perc`,sum(`profit`.`usd_profit`) AS `usd_profit`,sum(`profit`.`usd_net_profit`) AS `usd_net_profit`,count(0) AS `count` from `greencandle`.`profit` where `profit`.`perc` is not null group by left(`profit`.`close_time`,10) order by left(`profit`.`close_time`,10) desc;
