# 4.9

drop view if exists profitable_by_name_pair;
create view profitable_by_name_pair as
select `profit`.`name` AS `name`,`profit`.`pair` AS `pair`,count(0) AS `total`,sum(case when `profit`.`perc` > 0 then 1 else 0 end) AS `profit`,sum(case when `profit`.`net_perc` > 0 then 1 else 0 end) AS `net_profit`,sum(case when `profit`.`net_perc` < 0 then 1 else 0 end) AS `net_loss`,sum(case when `profit`.`perc` > 0 then 1 else 0 end) / count(0) * 100 AS `perc_profitable`,sum(case when `profit`.`net_perc` > 0 then 1 else 0 end) / count(0) * 100 AS `net_perc_profitable`,sum(`profit`.`perc`) AS `total_perc`,sum(`profit`.`perc`) / count(0) AS `per_trade`,sum(`profit`.`net_perc`) AS `total_net_perc`,sum(`profit`.`net_perc`) / count(0) AS `net_per_trade`,max(`profit`.`perc`) AS `max(perc)`,min(`profit`.`perc`) AS `min(perc)`,max(`profit`.`net_perc`) AS `max(net_perc)`,min(`profit`.`net_perc`) AS `min(net_perc)` from `greencandle`.`profit` group by `profit`.`name`,`profit`.`pair` order by cast(`profit`.`open_time` as date) desc

drop function if exists get_var;
CREATE FUNCTION `get_var`(name VARCHAR(30)) RETURNS varchar(30)
RETURN (select value from variables where name=name LIMIT 1);

ALTER TABLE variables ADD UNIQUE (name);

REPLACE into variables (name, value) VALUES ('start_time', '01:30');
REPLACE into variables (name, value) VALUES ('end_time', '08:30');

drop view if exists profit_pair_time;
create view profit_pair_time as select `profit`.`name` AS `name`,pair,count(0) AS `total`,sum(case when `profit`.`perc` > 0 then 1 else 0 end) AS `profit`,sum(case when `profit`.`net_perc` > 0 then 1 else 0 end) AS `net_profit`,sum(case when `profit`.`net_perc` < 0 then 1 else 0 end) AS `net_loss`,sum(case when `profit`.`perc` > 0 then 1 else 0 end) / count(0) * 100 AS `perc_profitable`,sum(case when `profit`.`net_perc` > 0 then 1 else 0 end) / count(0) * 100 AS `net_perc_profitable`,sum(`profit`.`perc`) AS `total_perc`,sum(`profit`.`perc`) / count(0) AS `per_trade`,sum(`profit`.`net_perc`) AS `total_net_perc`,sum(`profit`.`net_perc`) / count(0) AS `net_per_trade`,max(`profit`.`perc`) AS `max(perc)`,min(`profit`.`perc`) AS `min(perc)`,max(`profit`.`net_perc`) AS `max(net_perc)`,min(`profit`.`net_perc`) AS `min(net_perc)` from `greencandle`.`profit` where time(open_time) not between get_var('start_time') and get_var('end_time') group by `profit`.`name`,pair order by cast(`profit`.`open_time` as date) desc;
