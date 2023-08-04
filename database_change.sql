# 6.17

drop view if exists profit_daily;
drop view if exists profit_pair_time;
drop view if exists profitable_by_name_pair;
drop view if exists profitable_week;
drop view if exists profit_daily_by_quote_pair;

drop view if exists daily_profit_breakdown;
drop view if exists profit_by_dayname_diretion;
drop procedure if exists GetProfitableByDayName;

create view daily_profit_breakdown as
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
 	FROM daily_profit_breakdown
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

