# 6.30

drop table if exists commission_paid;
CREATE TABLE `commission_paid` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `date` datetime DEFAULT current_timestamp(),
  `asset` varchar(30) DEFAULT NULL,
  `usd_amt` decimal(15,2),
  `gbp_amt` decimal(15,2),
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=39669 DEFAULT CHARSET=latin1;


