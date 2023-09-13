# 6.36

# reopen a trade in mysql
CREATE FUNCTION `REOPEN_TRADE`(reopen_id int(11)) RETURNS int(11)
    DETERMINISTIC
BEGIN
			UPDATE
	trades
SET
	close_time = '0000-00-00 00:00:00',
	close_price = NULL,
	base_out = NULL,
	quote_out = NULL,
	closed_by = NULL,
	drawdown_perc = NULL,
	drawup_perc = NULL,
	close_usd_rate = NULL,
	close_gbp_rate = NULL,
	comm_close = NULL,
	close_order_id = NULL,
	COMMENT = NULL
WHERE
	id =reopen_id;
RETURN 1;
END;
