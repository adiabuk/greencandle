-- MySQL dump 10.13  Distrib 5.7.38, for Linux (x86_64)
--
-- Host: 10.8.0.104    Database: greencandle
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
-- Temporary table structure for view `accounts`
--

DROP TABLE IF EXISTS `accounts`;
/*!50001 DROP VIEW IF EXISTS `accounts`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE VIEW `accounts` AS SELECT 
 1 AS `open_time`,
 1 AS `close_time`,
 1 AS `open_price`,
 1 AS `close_price`,
 1 AS `perc`,
 1 AS `borrowed`,
 1 AS `profit`,
 1 AS `pair`,
 1 AS `quote_pair`,
 1 AS `name`,
 1 AS `quote_out`,
 1 AS `quote_in`,
 1 AS `amount`*/;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `api_requests`
--

DROP TABLE IF EXISTS `api_requests`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `api_requests` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `date` datetime DEFAULT CURRENT_TIMESTAMP,
  `pair` varchar(30) DEFAULT NULL,
  `text` varchar(100) DEFAULT NULL,
  `action` varchar(30) DEFAULT NULL,
  `price` varchar(30) DEFAULT NULL,
  `strategy` varchar(30) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=556 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

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
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
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
 1 AS `perc`,
 1 AS `usd_profit`,
 1 AS `count(*)`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `daily_profit_by_base_pair`
--

DROP TABLE IF EXISTS `daily_profit_by_base_pair`;
/*!50001 DROP VIEW IF EXISTS `daily_profit_by_base_pair`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE VIEW `daily_profit_by_base_pair` AS SELECT 
 1 AS `base_pair`,
 1 AS `date`,
 1 AS `perc`,
 1 AS `pairs`,
 1 AS `count`,
 1 AS `usd_profit`*/;
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
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Temporary table structure for view `hourly_profit`
--

DROP TABLE IF EXISTS `hourly_profit`;
/*!50001 DROP VIEW IF EXISTS `hourly_profit`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE VIEW `hourly_profit` AS SELECT 
 1 AS `date`,
 1 AS `hour`,
 1 AS `total_perc`,
 1 AS `avg_perc`,
 1 AS `usd_profit`,
 1 AS `num_trades`*/;
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
 1 AS `usd_profit`,
 1 AS `perc`,
 1 AS `count(*)`*/;
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
  `name` varchar(30) DEFAULT NULL,
  `interval` varchar(3) DEFAULT NULL,
  `usd_quantity` varchar(30) DEFAULT NULL
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
 1 AS `id`,
 1 AS `open_time`,
 1 AS `interval`,
 1 AS `close_time`,
 1 AS `pair`,
 1 AS `name`,
 1 AS `open_price`,
 1 AS `close_price`,
 1 AS `perc`,
 1 AS `quote_profit`,
 1 AS `drawdown_perc`,
 1 AS `drawup_perc`,
 1 AS `usd_profit`*/;
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
 1 AS `perc_profitable`,
 1 AS `perc`,
 1 AS `per_trade`,
 1 AS `max(perc)`,
 1 AS `min(perc)`*/;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `trades`
--

DROP TABLE IF EXISTS `trades`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `trades` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `open_time` timestamp NULL DEFAULT '0000-00-00 00:00:00',
  `close_time` timestamp NULL DEFAULT '0000-00-00 00:00:00',
  `pair` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `interval` varchar(3) DEFAULT NULL,
  `open_price` varchar(30) DEFAULT NULL,
  `close_price` varchar(30) DEFAULT NULL,
  `base_in` varchar(30) DEFAULT NULL,
  `base_out` varchar(30) DEFAULT NULL,
  `quote_in` varchar(30) DEFAULT NULL,
  `quote_out` varchar(30) DEFAULT NULL,
  `name` varchar(30) DEFAULT NULL,
  `closed_by` varchar(30) DEFAULT NULL,
  `drawdown_perc` varchar(4) DEFAULT NULL,
  `borrowed` varchar(30) DEFAULT '0',
  `multiplier` varchar(3) DEFAULT '0',
  `direction` varchar(30) DEFAULT NULL,
  `drawup_perc` varchar(4) DEFAULT NULL,
  `open_usd_rate` varchar(30) DEFAULT NULL,
  `open_gbp_rate` varchar(30) DEFAULT NULL,
  `close_usd_rate` varchar(30) DEFAULT NULL,
  `close_gbp_rate` varchar(30) DEFAULT NULL,
  `comm_open` varchar(255) DEFAULT NULL,
  `comm_close` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=109 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Temporary table structure for view `weekly_profit`
--

DROP TABLE IF EXISTS `weekly_profit`;
/*!50001 DROP VIEW IF EXISTS `weekly_profit`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE VIEW `weekly_profit` AS SELECT 
 1 AS `week_name`,
 1 AS `YEAR(close_time)`,
 1 AS `WEEK(close_time)`,
 1 AS `COUNT(*)`,
 1 AS `date`,
 1 AS `usd_profit`,
 1 AS `perc`*/;
SET character_set_client = @saved_cs_client;

--
-- Final view structure for view `accounts`
--

/*!50001 DROP VIEW IF EXISTS `accounts`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`%` SQL SECURITY DEFINER */
/*!50001 VIEW `accounts` AS select `p`.`open_time` AS `open_time`,`t`.`close_time` AS `close_time`,`t`.`open_price` AS `open_price`,`t`.`close_price` AS `close_price`,`p`.`perc` AS `perc`,`t`.`borrowed` AS `borrowed`,`p`.`quote_profit` AS `profit`,`t`.`pair` AS `pair`,(case when (`t`.`pair` like '%BTC') then 'BTC' when (`t`.`pair` like '%BNB') then 'BNB' when (`t`.`pair` like '%ETH') then 'ETH' when (`t`.`pair` like '%USDT') then 'USDT' end) AS `quote_pair`,`t`.`name` AS `name`,`t`.`base_out` AS `quote_out`,`t`.`base_in` AS `quote_in`,`t`.`quote_in` AS `amount` from (`trades` `t` join `profit` `p`) where ((`p`.`id` = `t`.`id`) and (`t`.`close_price` is not null)) */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

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
/*!50001 VIEW `daily_profit` AS select left(`profit`.`close_time`,10) AS `date`,sum(`profit`.`perc`) AS `perc`,sum(`profit`.`usd_profit`) AS `usd_profit`,count(0) AS `count(*)` from `profit` where (`profit`.`perc` is not null) group by left(`profit`.`close_time`,10) order by left(`profit`.`close_time`,10) desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `daily_profit_by_base_pair`
--

/*!50001 DROP VIEW IF EXISTS `daily_profit_by_base_pair`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`%` SQL SECURITY DEFINER */
/*!50001 VIEW `daily_profit_by_base_pair` AS select (case when (`profit`.`pair` like '%BTC') then 'BTC' when (`profit`.`pair` like '%BNB') then 'BNB' when (`profit`.`pair` like '%ETH') then 'ETH' when (`profit`.`pair` like '%USDT') then 'USDT' end) AS `base_pair`,left(`profit`.`close_time`,10) AS `date`,sum(`profit`.`perc`) AS `perc`,group_concat(distinct `profit`.`pair` separator ' ') AS `pairs`,count(0) AS `count`,(case when (`profit`.`pair` like '%BTC') then (sum(`profit`.`quote_profit`) * 50730.01000000) when (`profit`.`pair` like '%BNB') then (sum(`profit`.`quote_profit`) * 606.24000000) when (`profit`.`pair` like '%ETH') then (sum(`profit`.`quote_profit`) * 4083.72000000) when (`profit`.`pair` like '%USDT') then sum(`profit`.`quote_profit`) end) AS `usd_profit` from `profit` where (not((`profit`.`close_time` like '%0000-00-00%'))) group by left(`profit`.`close_time`,10),right(`profit`.`pair`,3) order by `profit`.`close_time` desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `hourly_profit`
--

/*!50001 DROP VIEW IF EXISTS `hourly_profit`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`%` SQL SECURITY DEFINER */
/*!50001 VIEW `hourly_profit` AS select date_format(`profit`.`close_time`,'%Y-%m-%d') AS `date`,date_format(`profit`.`close_time`,'%H') AS `hour`,sum(`profit`.`perc`) AS `total_perc`,avg(`profit`.`perc`) AS `avg_perc`,sum(`profit`.`usd_profit`) AS `usd_profit`,count(0) AS `num_trades` from `profit` where (year(`profit`.`close_time`) <> 0) group by hour(`profit`.`close_time`),dayofmonth(`profit`.`close_time`),month(`profit`.`close_time`),year(`profit`.`close_time`) order by `profit`.`close_time` desc */;
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
/*!50001 VIEW `monthly_profit` AS select left(`profit`.`close_time`,7) AS `date`,sum(`profit`.`usd_profit`) AS `usd_profit`,sum(`profit`.`perc`) AS `perc`,count(0) AS `count(*)` from `profit` where (`profit`.`perc` is not null) group by left(`profit`.`close_time`,7) order by left(`profit`.`close_time`,7) desc,sum(`profit`.`quote_profit`) */;
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
/*!50001 VIEW `profit` AS select `trades`.`id` AS `id`,`trades`.`open_time` AS `open_time`,`trades`.`interval` AS `interval`,`trades`.`close_time` AS `close_time`,`trades`.`pair` AS `pair`,`trades`.`name` AS `name`,`trades`.`open_price` AS `open_price`,`trades`.`close_price` AS `close_price`,(case when (`trades`.`direction` = 'long') then (((`trades`.`quote_out` - `trades`.`quote_in`) / `trades`.`quote_in`) * 100) else (((`trades`.`open_price` - `trades`.`close_price`) / `trades`.`open_price`) * 100) end) AS `perc`,(case when (`trades`.`direction` = 'long') then (`trades`.`quote_out` - `trades`.`quote_in`) else (`trades`.`quote_in` - `trades`.`quote_out`) end) AS `quote_profit`,`trades`.`drawdown_perc` AS `drawdown_perc`,`trades`.`drawup_perc` AS `drawup_perc`,(case when (`trades`.`direction` = 'long') then ((`trades`.`quote_out` - `trades`.`quote_in`) * `trades`.`close_usd_rate`) else ((`trades`.`quote_in` - `trades`.`quote_out`) * `trades`.`close_usd_rate`) end) AS `usd_profit` from `trades` */;
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
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`%` SQL SECURITY DEFINER */
/*!50001 VIEW `profitable` AS select `profit`.`pair` AS `pair`,count(0) AS `total`,sum((case when (`profit`.`perc` > 0) then 1 else 0 end)) AS `profit`,sum((case when (`profit`.`perc` < 0) then 1 else 0 end)) AS `loss`,((sum((case when (`profit`.`perc` > 0) then 1 else 0 end)) / count(0)) * 100) AS `perc_profitable`,sum(`profit`.`perc`) AS `perc`,(sum(`profit`.`perc`) / count(0)) AS `per_trade`,max(`profit`.`perc`) AS `max(perc)`,min(`profit`.`perc`) AS `min(perc)` from `profit` where (month(`profit`.`close_time`) = month(curdate())) group by `profit`.`pair` order by ((sum((case when (`profit`.`perc` > 0) then 1 else 0 end)) / count(0)) * 100) desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `weekly_profit`
--

/*!50001 DROP VIEW IF EXISTS `weekly_profit`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`%` SQL SECURITY DEFINER */
/*!50001 VIEW `weekly_profit` AS select concat(year(`profit`.`close_time`),'/',week(`profit`.`close_time`)) AS `week_name`,year(`profit`.`close_time`) AS `YEAR(close_time)`,week(`profit`.`close_time`) AS `WEEK(close_time)`,count(0) AS `COUNT(*)`,left(`profit`.`close_time`,7) AS `date`,sum(`profit`.`usd_profit`) AS `usd_profit`,sum(`profit`.`perc`) AS `perc` from `profit` group by concat(year(`profit`.`close_time`),'/',week(`profit`.`close_time`)) order by year(`profit`.`close_time`) desc,week(`profit`.`close_time`) desc */;
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

-- Dump completed on 2022-05-30 13:26:08
-- MySQL dump 10.13  Distrib 5.7.38, for Linux (x86_64)
--
-- Host: 10.8.0.104    Database: greencandle
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
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `exchange`
--

LOCK TABLES `exchange` WRITE;
/*!40000 ALTER TABLE `exchange` DISABLE KEYS */;
INSERT INTO `exchange` VALUES (3,'coinbase'),(4,'binance'),(5,'margin'),(6,'phemex'),(7,'isolated');
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

-- Dump completed on 2022-05-30 13:26:09
