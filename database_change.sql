use greencandle;

CREATE TABLE if not exists `balance_summary` (
  `ctime` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `usd` double DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;




