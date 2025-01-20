# 8.9

RENAME TABLE if exists profit_by_dayname_diretion to profit_by_dayname_direction;


drop view if exists profit_by_direction;
create view profit_by_direction as
SELECT
  date(`profit`.`open_time`) AS `day`,
  sum(`profit`.`net_perc`) AS `net_perc`,
  `profit`.`direction` AS `direction`,
  sum(
    CASE
      WHEN `profit`.`net_perc` > 0 THEN 1
      ELSE 0
    END
  ) / count(0) * 100 AS `net_perc_profitable`
FROM
  `greencandle`.`profit`
GROUP BY
  date(`profit`.`open_time`),
  `profit`.`direction`
ORDER BY
  date(open_time) desc;


drop view if exists profit_by_direction_hour;
create view profit_by_direction_hour as
SELECT
  date(`profit`.`open_time`) AS `day`,
  hour(`profit`.`open_time`) AS `hour`,
  sum(`profit`.`net_perc`) AS `net_perc`,
  `profit`.`direction` AS `direction`,
  sum(
    CASE
      WHEN `profit`.`net_perc` > 0 THEN 1
      ELSE 0
    END
  ) / count(0) * 100 AS `net_perc_profitable`
FROM
  `greencandle`.`profit`
GROUP BY
  date(`profit`.`open_time`),
  `profit`.`direction`,
  hour(`profit`.`open_time`)
ORDER BY
  date(open_time) desc;


