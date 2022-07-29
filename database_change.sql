-- Version 3.26

rename table if exists profitable_by_date to profitable_daily;

drop view if exists profit_daily;
drop table if exists profit_daily;
create view profit_daily as
select left(`profit`.`close_time`,10) AS `date`,dayname(`profit`.`close_time`) AS `day`,sum(`profit`.`perc`) AS `total_perc`,avg(`profit`.`perc`) AS `avg_perc`,sum(`profit`.`usd_profit`) AS `usd_profit`,count(0) AS `count` from `greencandle`.`profit` where `profit`.`perc` is not null group by left(`profit`.`close_time`,10) order by left(`profit`.`close_time`,10) desc;
