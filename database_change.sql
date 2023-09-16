# 6.38

# add filter for profit views
create or replace view profit as
SELECT
	`greencandle`.`trades`.`id` AS `id`,
	dayname(`greencandle`.`trades`.`open_time`) AS `day`,
	`greencandle`.`trades`.`open_time` AS `open_time`,
	`greencandle`.`trades`.`interval` AS `interval`,
	`greencandle`.`trades`.`close_time` AS `close_time`,
	`greencandle`.`trades`.`pair` AS `pair`,
	`greencandle`.`trades`.`name` AS `name`,
	`greencandle`.`trades`.`open_price` AS `open_price`,
	`greencandle`.`trades`.`close_price` AS `close_price`,
	cast(`PERC_DIFF` (`greencandle`.`trades`.`direction`, `greencandle`.`trades`.`open_price`, `greencandle`.`trades`.`close_price`) AS decimal (12, 4)) AS `perc`,
	cast(`PERC_DIFF` (`greencandle`.`trades`.`direction`, `greencandle`.`trades`.`open_price`, `greencandle`.`trades`.`close_price`) - `commission` () AS decimal (12, 4)) AS `net_perc`,
	CASE WHEN `greencandle`.`trades`.`direction` = 'long' THEN
		`greencandle`.`trades`.`quote_out` - `greencandle`.`trades`.`quote_in`
	ELSE
		`greencandle`.`trades`.`quote_in` - `greencandle`.`trades`.`quote_out`
	END AS `quote_profit`,
	CASE WHEN `greencandle`.`trades`.`direction` = 'long' THEN
		`greencandle`.`trades`.`quote_out` - `add_percent` (`greencandle`.`trades`.`quote_in`,
			`commission` ())
	ELSE
		`remove_percent` (`greencandle`.`trades`.`quote_in`,
			`commission` ()) - `greencandle`.`trades`.`quote_out`
	END AS `quote_net_profit`,
	CASE WHEN `greencandle`.`trades`.`direction` = 'long' THEN
	(`greencandle`.`trades`.`quote_out` - `greencandle`.`trades`.`quote_in`) * `greencandle`.`trades`.`close_usd_rate`
ELSE
	(`greencandle`.`trades`.`quote_in` - `greencandle`.`trades`.`quote_out`) * `greencandle`.`trades`.`close_usd_rate`
	END AS `usd_profit`,
	CASE WHEN `greencandle`.`trades`.`direction` = 'long' THEN
	(`greencandle`.`trades`.`quote_out` - `add_percent` (`greencandle`.`trades`.`quote_in`,
			`commission` ())) * `greencandle`.`trades`.`close_usd_rate`
ELSE
	(`remove_percent` (`greencandle`.`trades`.`quote_in`,
			`commission` ()) - `greencandle`.`trades`.`quote_out`) * `greencandle`.`trades`.`close_usd_rate`
	END AS `usd_net_profit`,
	`greencandle`.`trades`.`quote_in` AS `quote_in`,
	`greencandle`.`trades`.`quote_out` AS `quote_out`,
	`greencandle`.`trades`.`base_in` AS `base_in`,
	`greencandle`.`trades`.`base_out` AS `base_out`,
	`greencandle`.`trades`.`drawup_perc` AS `drawup_perc`,
	`greencandle`.`trades`.`drawdown_perc` AS `drawdown_perc`,
	`greencandle`.`trades`.`borrowed` AS `borrowed`,
	`greencandle`.`trades`.`borrowed_usd` AS `borrowed_usd`,
	`greencandle`.`trades`.`divisor` AS `divisor`,
	`greencandle`.`trades`.`direction` AS `direction`,
	`greencandle`.`trades`.`open_usd_rate` AS `open_usd_rate`,
	`greencandle`.`trades`.`close_usd_rate` AS `close_usd_rate`,
	`greencandle`.`trades`.`open_gbp_rate` AS `open_gbp_rate`,
	`greencandle`.`trades`.`close_gbp_rate` AS `close_gbp_rate`,
	`greencandle`.`trades`.`comm_open` AS `comm_open`,
	`greencandle`.`trades`.`comm_close` AS `comm_close`,
	`greencandle`.`trades`.`comment` AS `comment`
FROM
	`greencandle`.`trades`
WHERE
	`greencandle`.`trades`.`close_price` IS NOT NULL
	AND `greencandle`.`trades`.`close_price` <> ''
	AND `greencandle`.`trades`.`name` like (select get_var('filter'))
ORDER BY
	`greencandle`.`trades`.`close_time` DESC;

REPLACE INTO `variables`
SET `name` = 'filter',
`value` = '%any3%';
