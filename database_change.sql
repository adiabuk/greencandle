# 6.30

# add new commision table
CREATE TABLE IF NOT EXISTS `commission_paid` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `date` datetime DEFAULT current_timestamp(),
  `asset` varchar(30) DEFAULT NULL,
  `asset_amt` varchar(30)  NOT NULL,
  `usd_amt` decimal(15,2)  NOT NULL,
  `gbp_amt` decimal(15,2)  NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=39670 DEFAULT CHARSET=latin1;


# cleanup profit_monthly view
drop view if exists profit_monthly;
create view profit_monthly as
select left(`profit`.`close_time`,7) AS `date`,sum(`profit`.`usd_profit`) AS `usd_profit`,sum(`profit`.`usd_net_profit`) AS `usd_net_profit`,sum(`profit`.`perc`) AS `perc`,sum(`profit`.`net_perc`) AS `net_perc`,count(0) AS `count` from `greencandle`.`profit` where `profit`.`perc` is not null and year(close_time) != '0000' group by left(`profit`.`close_time`,7) order by left(`profit`.`close_time`,7) desc,sum(`profit`.`quote_profit`);
