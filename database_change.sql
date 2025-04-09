# 9.2.2

drop view if exists profit_by_direction_hour;
drop view if exists profit_by_direction_hour_open;
drop view if exists profit_by_direction_hour_close;

create view profit_by_direction_hour_close as
select cast(`profit`.`close_time` as date) AS `day`,hour(`profit`.`close_time`) AS `hour`,sum(`profit`.`net_perc`) AS `net_perc`,`profit`.`interval` AS `interval`,`profit`.`direction` AS `direction`,sum(case when `profit`.`net_perc` > 0 then 1 else 0 end) / count(0) * 100 AS `net_perc_profitable` from `greencandle`.`profit` group by cast(`profit`.`close_time` as date),`profit`.`direction`,`profit`.`interval`,hour(`profit`.`close_time`) order by cast(`profit`.`close_time` as date) desc;

create view profit_by_direction_hour_open as
select cast(`profit`.`open_time` as date) AS `day`,hour(`profit`.`open_time`) AS `hour`,sum(`profit`.`net_perc`) AS `net_perc`,`profit`.`interval` AS `interval`,`profit`.`direction` AS `direction`,sum(case when `profit`.`net_perc` > 0 then 1 else 0 end) / count(0) * 100 AS `net_perc_profitable` from `greencandle`.`profit` group by cast(`profit`.`open_time` as date),`profit`.`direction`,`profit`.`interval`,hour(`profit`.`open_time`) order by cast(`profit`.`open_time` as date) desc;
