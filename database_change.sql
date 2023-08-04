# 6.17

drop view if exists profit_daily;
drop view if exists profit_pair_time;
drop view if exists profitable_by_name_pair;
drop view if exists profitable_week;
drop view if exists profit_daily_by_quote_pair;

drop view if exists daily_profit_breakdown;
drop view if exists profit_daily_breakdown;
drop view if exists profit_by_dayname_diretion;
drop procedure if exists GetProfitableByDayName;
drop view if exists profitable_totals;
drop view if exists profitable_today;
drop view if exists profitable_month;
drop view if exists profit;
drop view if exists profitable_daily;
drop view if exists profit_open_trades;

create view profit as select `greencandle`.`trades`.`id` AS `id`,dayname(`greencandle`.`trades`.`open_time`) AS `day`,`greencandle`.`trades`.`open_time` AS `open_time`,`greencandle`.`trades`.`interval` AS `interval`,`greencandle`.`trades`.`close_time` AS `close_time`,`greencandle`.`trades`.`pair` AS `pair`,`greencandle`.`trades`.`name` AS `name`,`greencandle`.`trades`.`open_price` AS `open_price`,`greencandle`.`trades`.`close_price` AS `close_price`,`PERC_DIFF`(`greencandle`.`trades`.`direction`,`greencandle`.`trades`.`open_price`,`greencandle`.`trades`.`close_price`) AS `perc`,`PERC_DIFF`(`greencandle`.`trades`.`direction`,`greencandle`.`trades`.`open_price`,`greencandle`.`trades`.`close_price`) - `commission`() AS `net_perc`,case when `greencandle`.`trades`.`direction` = 'long' then `greencandle`.`trades`.`quote_out` - `greencandle`.`trades`.`quote_in` else `greencandle`.`trades`.`quote_in` - `greencandle`.`trades`.`quote_out` end AS `quote_profit`,case when `greencandle`.`trades`.`direction` = 'long' then `greencandle`.`trades`.`quote_out` - `add_percent`(`greencandle`.`trades`.`quote_in`,`commission`()) else `remove_percent`(`greencandle`.`trades`.`quote_in`,`commission`()) - `greencandle`.`trades`.`quote_out` end AS `quote_net_profit`,case when `greencandle`.`trades`.`direction` = 'long' then (`greencandle`.`trades`.`quote_out` - `greencandle`.`trades`.`quote_in`) * `greencandle`.`trades`.`close_usd_rate` else (`greencandle`.`trades`.`quote_in` - `greencandle`.`trades`.`quote_out`) * `greencandle`.`trades`.`close_usd_rate` end AS `usd_profit`,case when `greencandle`.`trades`.`direction` = 'long' then (`greencandle`.`trades`.`quote_out` - `add_percent`(`greencandle`.`trades`.`quote_in`,`commission`())) * `greencandle`.`trades`.`close_usd_rate` else (`remove_percent`(`greencandle`.`trades`.`quote_in`,`commission`()) - `greencandle`.`trades`.`quote_out`) * `greencandle`.`trades`.`close_usd_rate` end AS `usd_net_profit`,`greencandle`.`trades`.`quote_in` AS `quote_in`,`greencandle`.`trades`.`quote_out` AS `quote_out`,`greencandle`.`trades`.`base_in` AS `base_in`,`greencandle`.`trades`.`base_out` AS `base_out`,`greencandle`.`trades`.`drawup_perc` AS `drawup_perc`,`greencandle`.`trades`.`drawdown_perc` AS `drawdown_perc`,`greencandle`.`trades`.`borrowed` AS `borrowed`,`greencandle`.`trades`.`borrowed_usd` AS `borrowed_usd`,`greencandle`.`trades`.`divisor` AS `divisor`,`greencandle`.`trades`.`direction` AS `direction`,`greencandle`.`trades`.`open_usd_rate` AS `open_usd_rate`,`greencandle`.`trades`.`close_usd_rate` AS `close_usd_rate`,`greencandle`.`trades`.`open_gbp_rate` AS `open_gbp_rate`,`greencandle`.`trades`.`close_gbp_rate` AS `close_gbp_rate`,`greencandle`.`trades`.`comm_open` AS `comm_open`,`greencandle`.`trades`.`comm_close` AS `comm_close` from `greencandle`.`trades` where `greencandle`.`trades`.`close_price` is not null and `greencandle`.`trades`.`close_price` <> '' order by `greencandle`.`trades`.`close_time` desc;
select cast(`profit`.`close_time` as date) AS `date`,dayname(`profit`.`close_time`) AS `day`,count(0) AS `total`,sum(case when `profit`.`perc` > 0 then 1 else 0 end) AS `profit`,sum(case when `profit`.`net_perc` > 0 then 1 else 0 end) AS `net_profit`,sum(case when `profit`.`perc` < 0 then 1 else 0 end) AS `loss`,sum(case when `profit`.`net_perc` < 0 then 1 else 0 end) AS `net_loss`,sum(case when `profit`.`perc` > 0 then 1 else 0 end) / count(0) * 100 AS `perc_profitable`,sum(case when `profit`.`net_perc` > 0 then 1 else 0 end) / count(0) * 100 AS `net_perc_profitable`,sum(`profit`.`perc`) AS `perc`,sum(`profit`.`perc`) / count(0) AS `per_trade`,sum(`profit`.`net_perc`) AS `net_perc`,sum(`profit`.`net_perc`) / count(0) AS `net_per_trade`,max(`profit`.`perc`) AS `max(perc)`,min(`profit`.`perc`) AS `min(perc)`,max(`profit`.`net_perc`) AS `max(net_perc)`,min(`profit`.`net_perc`) AS `min(net_perc)` from `greencandle`.`profit` where `profit`.`pair` is not null and cast(`profit`.`close_time` as date) <> '0000-00-00' group by cast(`profit`.`close_time` as date) order by `profit`.`close_time` desc;
create view profit_daily_breakdown as
select dayname(
	`profit`.`open_time`) AS `dayname`,
`profit`.`interval` AS `interval`,
cast(
	`profit`.`open_time` AS date) AS `date`,
`profit`.`name` AS `name`,
count(
	0) AS `count`,
sum(
	`profit`.`net_perc`) AS `net_perc`,
`profit`.`direction` AS `direction`,
sum(
	CASE WHEN `profit`.`net_perc` > 0 THEN
		1
	ELSE
		- 1
	END) / count(
	0) * 100 AS `net_perc_profitable`
FROM
	`greencandle`.`profit`
GROUP BY
	`profit`.`name`,
	`profit`.`direction`,
	cast(
		`profit`.`open_time` AS date)
ORDER BY
	cast(
		`profit`.`open_time` AS date)
	DESC,
	sum(
		`profit`.`net_perc`)
	DESC;

DELIMITER //

CREATE PROCEDURE GetProfitableByDayName(
	IN dayname VARCHAR(255), intervalx VARCHAR(255)
)
BEGIN
	SELECT name, sum(net_perc), direction, count(*)
 	FROM profit_daily_breakdown
	WHERE dayname = dayname and `interval` = intervalx
	group by name, direction
	order by sum(net_perc) desc;
END //

DELIMITER ;

create view profit_by_dayname_diretion as

	SELECT
		dayname(
			open_time) AS day_name,
	sum(
		net_perc),
	direction,
	sum(
		CASE WHEN net_perc > 0 THEN
			1
		ELSE
			0
		END) / count(
		0) * 100 AS `net_perc_profitable`
FROM
	profit
GROUP BY
	dayname(
		open_time),
	direction
ORDER BY
	FIELD(
		`day`, 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
);
ALTER TABLE trades ADD COLUMN IF NOT EXISTS comment VARCHAR(255);

create profit_open_trades as
select name, sum(net_perc) as net_perc, direction, count(*) as count from open_trades group by name, direction order by net_perc desc;

