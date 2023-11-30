# 6.45

create or replace view profit_daily_by_close as
SELECT
	cast(`profit`.`close_time` AS date) AS `date`,
	dayname(`profit`.`close_time`) AS `day`,
	sum(cast(`profit`.`net_perc` AS decimal (12, 2))) AS `sum_net_perc`,
	avg(cast(`profit`.`net_perc` AS decimal (12, 2))) AS `avg_net_perc`,
	max(cast(`profit`.`net_perc` AS decimal (12, 2))) AS `max_net_perc`,
	min(cast(`profit`.`net_perc` AS decimal (12, 2))) AS `min_net_perc`,
	count(0) AS `count`,
	sum(
		CASE WHEN `profit`.`net_perc` < 0 THEN
			1
		ELSE
			0
		END) AS `net_loss`,
	sum(
		CASE WHEN `profit`.`net_perc` > 0 THEN
			1
		ELSE
			0
		END) / count(0) * 100 AS `perc_profitable`,
	sum(
		CASE WHEN `profit`.`net_perc` > 0 THEN
			1
		ELSE
			0
		END) / count(0) * 100 AS `net_perc_profitable`,
	sum(cast(`profit`.`usd_net_profit` AS decimal (12, 2))) AS `usd_net_profit`
FROM
	`greencandle`.`profit`
GROUP BY
	cast(`profit`.`close_time` AS date)
ORDER BY
	cast(`profit`.`close_time` AS date)
	DESC;

create or replace view profit_daily_by_open as
SELECT
	cast(`profit`.`close_time` AS date) AS `date`,
	dayname(`profit`.`close_time`) AS `day`,
	sum(cast(`profit`.`net_perc` AS decimal (12, 2))) AS `sum_net_perc`,
	avg(cast(`profit`.`net_perc` AS decimal (12, 2))) AS `avg_net_perc`,
	max(cast(`profit`.`net_perc` AS decimal (12, 2))) AS `max_net_perc`,
	min(cast(`profit`.`net_perc` AS decimal (12, 2))) AS `min_net_perc`,
	count(0) AS `count`,
	sum(
		CASE WHEN `profit`.`net_perc` < 0 THEN
			1
		ELSE
			0
		END) AS `net_loss`,
	sum(
		CASE WHEN `profit`.`net_perc` > 0 THEN
			1
		ELSE
			0
		END) / count(0) * 100 AS `perc_profitable`,
	sum(
		CASE WHEN `profit`.`net_perc` > 0 THEN
			1
		ELSE
			0
		END) / count(0) * 100 AS `net_perc_profitable`,
	sum(cast(`profit`.`usd_net_profit` AS decimal (12, 2))) AS `usd_net_profit`
FROM
	`greencandle`.`profit`
GROUP BY
	cast(`profit`.`open_time` AS date)
ORDER BY
	cast(`profit`.`open_time` AS date)
	DESC;

drop view if exists profit_daily;
