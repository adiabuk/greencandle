-- MySQL dump 10.13  Distrib 5.7.32, for Linux (x86_64)
--
-- Host: localhost    Database: greencandle
-- ------------------------------------------------------
-- Server version	5.5.5-10.1.24-MariaDB-1~jessie

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `balance`
--

DROP TABLE IF EXISTS `balance`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `balance` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `ctime` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `exchange_id` int(11) unsigned NOT NULL,
  `gbp` varchar(30) DEFAULT NULL,
  `btc` varchar(30) DEFAULT NULL,
  `usd` varchar(30) DEFAULT NULL,
  `count` varchar(30) DEFAULT NULL,
  `coin` varchar(30) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `exchange_id` (`exchange_id`),
  CONSTRAINT `balance_ibfk_2` FOREIGN KEY (`exchange_id`) REFERENCES `exchange` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=285 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `balance_summary`
--

DROP TABLE IF EXISTS `balance_summary`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `balance_summary` (
  `ctime` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `usd` double DEFAULT NULL,
  `btc` varchar(30) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Temporary table structure for view `daily_profit`
--

DROP TABLE IF EXISTS `daily_profit`;
/*!50001 DROP VIEW IF EXISTS `daily_profit`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE VIEW `daily_profit` AS SELECT
 1 AS `date`,
 1 AS `perc`*/;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `exchange`
--

DROP TABLE IF EXISTS `exchange`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `exchange` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(10) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Temporary table structure for view `hour_balance`
--

DROP TABLE IF EXISTS `hour_balance`;
/*!50001 DROP VIEW IF EXISTS `hour_balance`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE VIEW `hour_balance` AS SELECT
 1 AS `exchange_id`,
 1 AS `usd1`,
 1 AS `coin`,
 1 AS `ctime1`,
 1 AS `ctime2`,
 1 AS `usd2`,
 1 AS `USD_diff`,
 1 AS `GBP_diff`,
 1 AS `COUNT_diff`,
 1 AS `perc_change`,
 1 AS `BTC_diff`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `monthly_profit`
--

DROP TABLE IF EXISTS `monthly_profit`;
/*!50001 DROP VIEW IF EXISTS `monthly_profit`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE VIEW `monthly_profit` AS SELECT
 1 AS `date`,
 1 AS `interval`,
 1 AS `profit`,
 1 AS `perc`*/;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `open_trades`
--

DROP TABLE IF EXISTS `open_trades`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `open_trades` (
  `pair` varchar(30) DEFAULT NULL,
  `open_price` varchar(30) DEFAULT NULL,
  `open_time` varchar(30) DEFAULT NULL,
  `current_price` varchar(30) DEFAULT NULL,
  `perc` varchar(30) DEFAULT NULL,
  `interval` varchar(3) DEFAULT NULL,
  `name` varchar(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Temporary table structure for view `profit`
--

DROP TABLE IF EXISTS `profit`;
/*!50001 DROP VIEW IF EXISTS `profit`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE VIEW `profit` AS SELECT
 1 AS `open_time`,
 1 AS `interval`,
 1 AS `close_time`,
 1 AS `pair`,
 1 AS `name`,
 1 AS `open_price`,
 1 AS `close_price`,
 1 AS `perc`,
 1 AS `base_profit`,
 1 AS `drawdown_perc`,
 1 AS `drawup_perc`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `profitable`
--

DROP TABLE IF EXISTS `profitable`;
/*!50001 DROP VIEW IF EXISTS `profitable`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE VIEW `profitable` AS SELECT
 1 AS `pair`,
 1 AS `total`,
 1 AS `profit`,
 1 AS `loss`,
 1 AS `perc_profitable`*/;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `trades`
--

DROP TABLE IF EXISTS `trades`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `trades` (
  `open_time` timestamp NULL DEFAULT '0000-00-00 00:00:00',
  `close_time` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  `pair` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `interval` varchar(3) DEFAULT NULL,
  `open_price` varchar(60) DEFAULT NULL,
  `close_price` varchar(30) DEFAULT NULL,
  `base_in` varchar(30) DEFAULT NULL,
  `base_out` varchar(30) DEFAULT NULL,
  `quote_in` varchar(30) DEFAULT NULL,
  `quote_out` varchar(30) DEFAULT NULL,
  `name` varchar(30) DEFAULT NULL,
  `borrowed` varchar(30) DEFAULT NULL,
  `multiplier` varchar(3) DEFAULT NULL,
  `closed_by` varchar(30) DEFAULT NULL,
  `drawdown_perc` varchar(4) DEFAULT NULL,
  `direction` varchar(5) DEFAULT NULL,
  `drawup_perc` varchar(4) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Final view structure for view `daily_profit`
--

/*!50001 DROP VIEW IF EXISTS `daily_profit`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`%` SQL SECURITY DEFINER */
/*!50001 VIEW `daily_profit` AS select left(`profit`.`close_time`,10) AS `date`,sum(`profit`.`perc`) AS `perc` from `profit` where (`profit`.`perc` is not null) group by left(`profit`.`close_time`,10) order by left(`profit`.`close_time`,10),sum(`profit`.`base_profit`) */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `hour_balance`
--

/*!50001 DROP VIEW IF EXISTS `hour_balance`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8 */;
/*!50001 SET character_set_results     = utf8 */;
/*!50001 SET collation_connection      = utf8_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `hour_balance` AS select `tt1`.`exchange_id` AS `exchange_id`,`tt1`.`usd` AS `usd1`,`tt1`.`coin` AS `coin`,`tt1`.`ctime` AS `ctime1`,`tt2`.`ctime` AS `ctime2`,`tt2`.`usd` AS `usd2`,(`tt1`.`usd` - `tt2`.`usd`) AS `USD_diff`,(`tt1`.`gbp` - `tt2`.`gbp`) AS `GBP_diff`,(`tt1`.`count` - `tt2`.`count`) AS `COUNT_diff`,(((`tt1`.`btc` - `tt2`.`btc`) / `tt1`.`btc`) * 100) AS `perc_change`,(`tt1`.`btc` - `tt2`.`btc`) AS `BTC_diff` from (`balance` `tt1` left join `balance` `tt2` on(((`tt1`.`coin` = `tt2`.`coin`) and (`tt1`.`exchange_id` = `tt2`.`exchange_id`)))) where ((`tt1`.`ctime` > (now() - interval 20 minute)) and (`tt2`.`ctime` < (now() - interval 45 minute)) and (`tt2`.`ctime` > (now() - interval 90 minute))) */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `monthly_profit`
--

/*!50001 DROP VIEW IF EXISTS `monthly_profit`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`%` SQL SECURITY DEFINER */
/*!50001 VIEW `monthly_profit` AS select left(`profit`.`close_time`,7) AS `date`,`profit`.`interval` AS `interval`,sum(`profit`.`base_profit`) AS `profit`,sum(`profit`.`perc`) AS `perc` from `profit` where (`profit`.`perc` is not null) group by left(`profit`.`close_time`,7) order by left(`profit`.`close_time`,7),sum(`profit`.`base_profit`) */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `profit`
--

/*!50001 DROP VIEW IF EXISTS `profit`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`%` SQL SECURITY DEFINER */
/*!50001 VIEW `profit` AS select `trades`.`open_time` AS `open_time`,`trades`.`interval` AS `interval`,`trades`.`close_time` AS `close_time`,`trades`.`pair` AS `pair`,`trades`.`name` AS `name`,`trades`.`open_price` AS `open_price`,`trades`.`close_price` AS `close_price`,(case when (`trades`.`direction` = 'long') then (((`trades`.`base_out` - `trades`.`base_in`) / `trades`.`base_in`) * 100) else (((`trades`.`open_price` - `trades`.`close_price`) / `trades`.`open_price`) * 100) end) AS `perc`,(case when (`trades`.`direction` = 'long') then (`trades`.`base_out` - `trades`.`base_in`) else (`trades`.`base_in` - `trades`.`base_out`) end) AS `base_profit`,`trades`.`drawdown_perc` AS `drawdown_perc`,`trades`.`drawup_perc` AS `drawup_perc` from `trades` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `profitable`
--

/*!50001 DROP VIEW IF EXISTS `profitable`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8 */;
/*!50001 SET character_set_results     = utf8 */;
/*!50001 SET collation_connection      = utf8_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`%` SQL SECURITY DEFINER */
/*!50001 VIEW `profitable` AS select `profit`.`pair` AS `pair`,count(0) AS `total`,sum((case when (`profit`.`perc` > 0) then 1 else 0 end)) AS `profit`,sum((case when (`profit`.`perc` < 0) then 1 else 0 end)) AS `loss`,((sum((case when (`profit`.`perc` > 0) then 1 else 0 end)) / count(0)) * 100) AS `perc_profitable` from `profit` group by `profit`.`pair` order by ((sum((case when (`profit`.`perc` > 0) then 1 else 0 end)) / count(0)) * 100) desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2021-02-01 21:46:12
-- MySQL dump 10.13  Distrib 5.7.32, for Linux (x86_64)
--
-- Host: localhost    Database: greencandle
-- ------------------------------------------------------
-- Server version	5.5.5-10.1.24-MariaDB-1~jessie

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `exchange`
--

DROP TABLE IF EXISTS `exchange`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `exchange` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `name` varchar(10) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `exchange`
--

LOCK TABLES `exchange` WRITE;
/*!40000 ALTER TABLE `exchange` DISABLE KEYS */;
INSERT INTO `exchange` VALUES (3,'coinbase'),(4,'binance'),(5,'margin'),(6,'phemex');
/*!40000 ALTER TABLE `exchange` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2021-02-01 21:46:12
