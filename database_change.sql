# 6.59

# table for loans taken before trade open

drop table if exists extra_loans;
CREATE TABLE IF NOT EXISTS extra_loans (
    `id` int(	11)	NOT NULL AUTO_INCREMENT,
	`symbol` varchar(6)	DEFAULT NULL,
	`date_added` datetime DEFAULT current_timestamp(),
	`date_removed` datetime DEFAULT NULL,
	`borrowed` varchar(30) 	DEFAULT '0',
	`borrowed_usd` varchar(	30)	DEFAULT NULL,
	PRIMARY KEY (`id`)
	);
