# 6.30

drop table if exists commission_paid;
CREATE TABLE `commission_paid` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `date` datetime DEFAULT current_timestamp(),
  `asset` varchar(30) DEFAULT NULL,
  `asset_amt` varchar(30)  NOT NULL,
  `usd_amt` decimal(15,2)  NOT NULL,
  `gbp_amt` decimal(15,2)  NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=39670 DEFAULT CHARSET=latin1;

