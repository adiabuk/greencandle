# 9.2

drop view if exists profit_daily_breakdown_close;
create view profit_daily_breakdown_close as
SELECT
	dayname(`profit`.`close_time`) AS `dayname`,
	`profit`.`interval` AS `interval`,
	cast(`profit`.`close_time` AS DATE) AS `close_date`,
	`profit`.`name` AS `name`,
	count(0) AS `count`,
	sum(`profit`.`net_perc`) AS `net_perc`,
	`profit`.`direction` AS `direction`,
	sum(
	CASE
		WHEN `profit`.`perc` > 0 THEN 1
		ELSE 0
	END
) / count(0) * 100 AS `perc_profitable`,
sum(
	CASE
		WHEN `profit`.`net_perc` > 0 THEN 1
		ELSE 0
	END
) / count(0) * 100 AS `net_perc_profitable`
FROM
	`greencandle`.`profit`
GROUP BY
	`profit`.`name`,
	`profit`.`direction`,
	cast(`profit`.`close_time` AS DATE)
ORDER BY
	cast(`profit`.`close_time` AS DATE) DESC,
	sum(`profit`.`net_perc`) DESC;

drop view if exists profit_daily_breakdown_open;
create view profit_daily_breakdown_open as
SELECT
	dayname(`profit`.`open_time`) AS `dayname`,
	`profit`.`interval` AS `interval`,
	cast(`profit`.`open_time` AS DATE) AS `close_date`,
	`profit`.`name` AS `name`,
	count(0) AS `count`,
	sum(`profit`.`net_perc`) AS `net_perc`,
	`profit`.`direction` AS `direction`,
	sum(
	CASE
		WHEN `profit`.`perc` > 0 THEN 1
		ELSE 0
	END
) / count(0) * 100 AS `perc_profitable`,
sum(
	CASE
		WHEN `profit`.`net_perc` > 0 THEN 1
		ELSE 0
	END
) / count(0) * 100 AS `net_perc_profitable`
FROM
	`greencandle`.`profit`
GROUP BY
	`profit`.`name`,
	`profit`.`direction`,
	cast(`profit`.`open_time` AS DATE)
ORDER BY
	cast(`profit`.`open_time` AS DATE) DESC,
	sum(`profit`.`net_perc`) DESC;
