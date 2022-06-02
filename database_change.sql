-- Version 3.9



-- profitable current month
drop view if exists profitable_month;
 create view profitable_month as select `profit`.`pair` AS `pair`,count(0) AS `total`,sum((case when (`profit`.`perc` > 0) then 1 else 0 end)) AS `profit`,sum((case when (`profit`.`perc` < 0) then 1 else 0 end)) AS `loss`,((sum((case when (`profit`.`perc` > 0) then 1 else 0 end)) / count(0)) * 100) AS `perc_profitable`,sum(`profit`.`perc`) AS `perc`,(sum(`profit`.`perc`) / count(0)) AS `per_trade`,max(`profit`.`perc`) AS `max(perc)`,min(`profit`.`perc`) AS `min(perc)` from `profit` where (month(`profit`.`close_time`) = month(curdate())) group by `profit`.`pair` order by ((sum((case when (`profit`.`perc` > 0) then 1 else 0 end)) / count(0)) * 100) desc;

-- profitable today
drop view if exists profitable_today;
create view profitable_today as select `profit`.`pair` AS `pair`,count(0) AS `total`,sum((case when (`profit`.`perc` > 0) then 1 else 0 end)) AS `profit`,sum((case when (`profit`.`perc` < 0) then 1 else 0 end)) AS `loss`,((sum((case when (`profit`.`perc` > 0) then 1 else 0 end)) / count(0)) * 100) AS `perc_profitable`,sum(`profit`.`perc`) AS `perc`,(sum(`profit`.`perc`) / count(0)) AS `per_trade`,max(`profit`.`perc`) AS `max(perc)`,min(`profit`.`perc`) AS `min(perc)` from `profit` where (date(`profit`.`close_time`) = date(curdate())) group by `profit`.`pair` order by ((sum((case when (`profit`.`perc` > 0) then 1 else 0 end)) / count(0)) * 100) desc;


-- profitable all data
DROP VIEW if exists profitable;
DROP VIEW if exists profitable_all;
create view profitable_all as select `profit`.`pair` AS `pair`,count(0) AS `total`,sum((case when (`profit`.`perc` > 0) then 1 else 0 end)) AS `profit`,sum((case when (`profit`.`perc` < 0) then 1 else 0 end)) AS `loss`,((sum((case when (`profit`.`perc` > 0) then 1 else 0 end)) / count(0)) * 100) AS `perc_profitable`,sum(`profit`.`perc`) AS `perc`,(sum(`profit`.`perc`) / count(0)) AS `per_trade`,max(`profit`.`perc`) AS `max(perc)`,min(`profit`.`perc`) AS `min(perc)` from `profit` where pair is not NULL group by `profit`.`pair` order by ((sum((case when (`profit`.`perc` > 0) then 1 else 0 end)) / count(0)) * 100) desc;

-- profitable current week
DROP VIEW if exists profitable_week;
create view profitable_week as select `profit`.`pair` AS `pair`,count(0) AS `total`,sum((case when (`profit`.`perc` > 0) then 1 else 0 end)) AS `profit`,sum((case when (`profit`.`perc` < 0) then 1 else 0 end)) AS `loss`,((sum((case when (`profit`.`perc` > 0) then 1 else 0 end)) / count(0)) * 100) AS `perc_profitable`,sum(`profit`.`perc`) AS `perc`,(sum(`profit`.`perc`) / count(0)) AS `per_trade`,max(`profit`.`perc`) AS `max(perc)`,min(`profit`.`perc`) AS `min(perc)` from `profit` where (week(`profit`.`close_time`) = week(curdate())) and (year(`profit`.`close_time`) = year(curdate())) group by `profit`.`pair` order by ((sum((case when (`profit`.`perc` > 0) then 1 else 0 end)) / count(0)) * 100) desc;

-- profitable totals
drop view if exists profitable_totals;
create view profitable_totals as SELECT table_name, perc_profitable, total_perc, avg_perc, count
FROM (
      SELECT "today" as table_name, avg(perc_profitable) as perc_profitable, sum(perc)  as total_perc, avg(perc) as avg_perc, count(0) as count FROM profitable_today
UNION SELECT "month" as table_name, avg(perc_profitable) as perc_profitable, sum(perc) as total_perc, avg(perc) as avg_perc, count(0) as count FROM profitable_month
UNION SELECT "week" as table_name, avg(perc_profitable) as perc_profitable, sum(perc) as total_perc, avg(perc) as avg_perc, count(0) as count FROM profitable_week
UNION SELECT "all"   as table_name, avg(perc_profitable) as perc_profitable, sum(perc) as total_perc, avg(perc) as avg_perc, count(0) as count FROM profitable_all

) as x
GROUP BY table_name;

-- profitable by date
drop view if exists profitable_by_date;
create view profitable_by_date as select date(`profit`.`open_time`) as `date`,count(0) AS `total`,sum((case when (`profit`.`perc` > 0) then 1 else 0 end)) AS `profit`,sum((case when (`profit`.`perc` < 0) then 1 else 0 end)) AS `loss`,((sum((case when (`profit`.`perc` > 0) then 1 else 0 end)) / count(0)) * 100) AS `perc_profitable`,sum(`profit`.`perc`) AS `perc`,(sum(`profit`.`perc`) / count(0)) AS `per_trade`,max(`profit`.`perc`) AS `max(perc)`,min(`profit`.`perc`) AS `min(perc)` from `profit` where pair is not NULL group by date(`profit`.`open_time`) order by ((sum((case when (`profit`.`perc` > 0) then 1 else 0 end)) / count(0)) * 100) desc;
