-- MySQL dump 10.13  Distrib 5.7.26, for Linux (x86_64)
--
-- Host: localhost    Database: greencandle_test
-- ------------------------------------------------------
-- Server version	5.7.26

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
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `coin`
--

DROP TABLE IF EXISTS `coin`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `coin` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `symbol` varchar(10) DEFAULT NULL,
  `name` varchar(10) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Temporary table structure for view `daily_profit_15m`
--

DROP TABLE IF EXISTS `daily_profit_15m`;
/*!50001 DROP VIEW IF EXISTS `daily_profit_15m`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE VIEW `daily_profit_15m` AS SELECT 
 1 AS `date`,
 1 AS `profit`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `daily_profit_1h`
--

DROP TABLE IF EXISTS `daily_profit_1h`;
/*!50001 DROP VIEW IF EXISTS `daily_profit_1h`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE VIEW `daily_profit_1h` AS SELECT 
 1 AS `date`,
 1 AS `profit`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `daily_profit_1m`
--

DROP TABLE IF EXISTS `daily_profit_1m`;
/*!50001 DROP VIEW IF EXISTS `daily_profit_1m`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE VIEW `daily_profit_1m` AS SELECT 
 1 AS `date`,
 1 AS `profit`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `daily_profit_3m`
--

DROP TABLE IF EXISTS `daily_profit_3m`;
/*!50001 DROP VIEW IF EXISTS `daily_profit_3m`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE VIEW `daily_profit_3m` AS SELECT 
 1 AS `date`,
 1 AS `profit`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `daily_profit_5m`
--

DROP TABLE IF EXISTS `daily_profit_5m`;
/*!50001 DROP VIEW IF EXISTS `daily_profit_5m`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE VIEW `daily_profit_5m` AS SELECT 
 1 AS `date`,
 1 AS `profit`*/;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `data`
--

DROP TABLE IF EXISTS `data`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `data` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `symbol` varchar(10) DEFAULT NULL,
  `ctime` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `event` varchar(20) DEFAULT NULL,
  `direction` varchar(20) DEFAULT NULL,
  `data` varchar(1000) DEFAULT NULL,
  `difference` varchar(5) DEFAULT NULL,
  `resistance` varchar(1000) DEFAULT NULL,
  `support` varchar(1000) DEFAULT NULL,
  `buy` varchar(20) DEFAULT NULL,
  `sell` varchar(20) DEFAULT NULL,
  `market` varchar(20) DEFAULT NULL,
  `balance` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

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
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=latin1;
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
-- Temporary table structure for view `profit_15m`
--

DROP TABLE IF EXISTS `profit_15m`;
/*!50001 DROP VIEW IF EXISTS `profit_15m`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE VIEW `profit_15m` AS SELECT 
 1 AS `buy_time`,
 1 AS `sell_time`,
 1 AS `pair`,
 1 AS `buy_price`,
 1 AS `sell_price`,
 1 AS `total`,
 1 AS `perc`,
 1 AS `base_profit`,
 1 AS `profit`,
 1 AS `buy_bbp`,
 1 AS `sell_gbp`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `profit_1h`
--

DROP TABLE IF EXISTS `profit_1h`;
/*!50001 DROP VIEW IF EXISTS `profit_1h`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE VIEW `profit_1h` AS SELECT 
 1 AS `buy_time`,
 1 AS `sell_time`,
 1 AS `pair`,
 1 AS `buy_price`,
 1 AS `sell_price`,
 1 AS `total`,
 1 AS `perc`,
 1 AS `base_profit`,
 1 AS `profit`,
 1 AS `buy_bgp`,
 1 AS `sell_gbp`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `profit_1m`
--

DROP TABLE IF EXISTS `profit_1m`;
/*!50001 DROP VIEW IF EXISTS `profit_1m`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE VIEW `profit_1m` AS SELECT 
 1 AS `buy_time`,
 1 AS `sell_time`,
 1 AS `pair`,
 1 AS `buy_price`,
 1 AS `sell_price`,
 1 AS `total`,
 1 AS `perc`,
 1 AS `base_profit`,
 1 AS `profit`,
 1 AS `buy_bbp`,
 1 AS `sell_gbp`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `profit_3m`
--

DROP TABLE IF EXISTS `profit_3m`;
/*!50001 DROP VIEW IF EXISTS `profit_3m`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE VIEW `profit_3m` AS SELECT 
 1 AS `buy_time`,
 1 AS `sell_time`,
 1 AS `pair`,
 1 AS `buy_price`,
 1 AS `sell_price`,
 1 AS `total`,
 1 AS `perc`,
 1 AS `base_profit`,
 1 AS `profit`,
 1 AS `buy_bbp`,
 1 AS `sell_gbp`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `profit_5m`
--

DROP TABLE IF EXISTS `profit_5m`;
/*!50001 DROP VIEW IF EXISTS `profit_5m`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE VIEW `profit_5m` AS SELECT 
 1 AS `buy_time`,
 1 AS `sell_time`,
 1 AS `pair`,
 1 AS `buy_price`,
 1 AS `sell_price`,
 1 AS `total`,
 1 AS `perc`,
 1 AS `base_profit`,
 1 AS `profit`,
 1 AS `buy_bbp`,
 1 AS `sell_gbp`*/;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `symbols`
--

DROP TABLE IF EXISTS `symbols`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `symbols` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `symbol` varchar(10) DEFAULT NULL,
  `category` varchar(20) DEFAULT NULL,
  `maximum_leverage` int(11) DEFAULT NULL,
  `maximum_amount` int(11) DEFAULT NULL,
  `overnight_charge_long_percent` float DEFAULT NULL,
  `overnight_charge_short_percent` float DEFAULT NULL,
  `decimals` int(11) DEFAULT NULL,
  `timezone` varchar(80) DEFAULT NULL,
  `timezone_offset` varchar(10) DEFAULT NULL,
  `open_day` varchar(80) DEFAULT NULL,
  `open_time` time DEFAULT NULL,
  `close_day` varchar(80) DEFAULT NULL,
  `close_time` time DEFAULT NULL,
  `daily_break_start` time DEFAULT NULL,
  `daily_break_stop` time DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `symbol` (`symbol`),
  KEY `category` (`category`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `trades_15m`
--

DROP TABLE IF EXISTS `trades_15m`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `trades_15m` (
  `buy_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `sell_time` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  `pair` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `buy_price` decimal(10,10) DEFAULT NULL,
  `sell_price` decimal(10,10) DEFAULT NULL,
  `investment` varchar(5) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `total` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `trades_1h`
--

DROP TABLE IF EXISTS `trades_1h`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `trades_1h` (
  `buy_time` timestamp NULL DEFAULT '0000-00-00 00:00:00',
  `sell_time` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  `pair` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `buy_price` varchar(60) DEFAULT NULL,
  `sell_price` varchar(30) DEFAULT NULL,
  `investment` varchar(5) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `total` varchar(10) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `trades_1m`
--

DROP TABLE IF EXISTS `trades_1m`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `trades_1m` (
  `buy_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `sell_time` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  `pair` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `buy_price` decimal(10,10) DEFAULT NULL,
  `sell_price` decimal(10,10) DEFAULT NULL,
  `investment` varchar(5) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `total` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `trades_3m`
--

DROP TABLE IF EXISTS `trades_3m`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `trades_3m` (
  `buy_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `sell_time` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  `pair` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `buy_price` decimal(10,10) DEFAULT NULL,
  `sell_price` decimal(10,10) DEFAULT NULL,
  `investment` varchar(5) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `total` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `trades_5m`
--

DROP TABLE IF EXISTS `trades_5m`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `trades_5m` (
  `buy_time` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `sell_time` timestamp NOT NULL DEFAULT '0000-00-00 00:00:00',
  `pair` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `buy_price` decimal(10,10) DEFAULT NULL,
  `sell_price` decimal(10,10) DEFAULT NULL,
  `investment` varchar(5) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `total` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Final view structure for view `daily_profit_15m`
--

/*!50001 DROP VIEW IF EXISTS `daily_profit_15m`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8 */;
/*!50001 SET character_set_results     = utf8 */;
/*!50001 SET collation_connection      = utf8_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`%` SQL SECURITY DEFINER */
/*!50001 VIEW `daily_profit_15m` AS select left(`profit_15m`.`sell_time`,10) AS `date`,sum(`profit_15m`.`profit`) AS `profit` from `profit_15m` group by left(`profit_15m`.`sell_time`,10) order by `date` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `daily_profit_1h`
--

/*!50001 DROP VIEW IF EXISTS `daily_profit_1h`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8 */;
/*!50001 SET character_set_results     = utf8 */;
/*!50001 SET collation_connection      = utf8_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`%` SQL SECURITY DEFINER */
/*!50001 VIEW `daily_profit_1h` AS select left(`profit_1h`.`sell_time`,10) AS `date`,sum(`profit_1h`.`profit`) AS `profit` from `profit_1h` group by left(`profit_1h`.`sell_time`,10) order by `date` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `daily_profit_1m`
--

/*!50001 DROP VIEW IF EXISTS `daily_profit_1m`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8 */;
/*!50001 SET character_set_results     = utf8 */;
/*!50001 SET collation_connection      = utf8_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`%` SQL SECURITY DEFINER */
/*!50001 VIEW `daily_profit_1m` AS select left(`profit_1m`.`sell_time`,10) AS `date`,sum(`profit_1m`.`profit`) AS `profit` from `profit_1m` group by left(`profit_1m`.`sell_time`,10) order by `date` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `daily_profit_3m`
--

/*!50001 DROP VIEW IF EXISTS `daily_profit_3m`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8 */;
/*!50001 SET character_set_results     = utf8 */;
/*!50001 SET collation_connection      = utf8_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`%` SQL SECURITY DEFINER */
/*!50001 VIEW `daily_profit_3m` AS select left(`profit_3m`.`sell_time`,10) AS `date`,sum(`profit_3m`.`profit`) AS `profit` from `profit_3m` group by left(`profit_3m`.`sell_time`,10) order by `date` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `daily_profit_5m`
--

/*!50001 DROP VIEW IF EXISTS `daily_profit_5m`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8 */;
/*!50001 SET character_set_results     = utf8 */;
/*!50001 SET collation_connection      = utf8_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`%` SQL SECURITY DEFINER */
/*!50001 VIEW `daily_profit_5m` AS select left(`profit_5m`.`sell_time`,10) AS `date`,sum(`profit_5m`.`profit`) AS `profit` from `profit_5m` group by left(`profit_5m`.`sell_time`,10) order by `date` */;
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
-- Final view structure for view `profit_15m`
--

/*!50001 DROP VIEW IF EXISTS `profit_15m`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8 */;
/*!50001 SET character_set_results     = utf8 */;
/*!50001 SET collation_connection      = utf8_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`%` SQL SECURITY DEFINER */
/*!50001 VIEW `profit_15m` AS select `trades_15m`.`buy_time` AS `buy_time`,`trades_15m`.`sell_time` AS `sell_time`,`trades_15m`.`pair` AS `pair`,`trades_15m`.`buy_price` AS `buy_price`,`trades_15m`.`sell_price` AS `sell_price`,`trades_15m`.`total` AS `total`,(((`trades_15m`.`sell_price` - `trades_15m`.`buy_price`) / `trades_15m`.`sell_price`) * 100) AS `perc`,(`trades_15m`.`sell_price` - `trades_15m`.`buy_price`) AS `base_profit`,(((`trades_15m`.`sell_price` - `trades_15m`.`buy_price`) * 8223.25) * `trades_15m`.`total`) AS `profit`,((`trades_15m`.`buy_price` * `trades_15m`.`total`) * 8223.25) AS `buy_bbp`,((`trades_15m`.`sell_price` * `trades_15m`.`total`) * 8223.25) AS `sell_gbp` from `trades_15m` order by (((`trades_15m`.`sell_price` - `trades_15m`.`buy_price`) / `trades_15m`.`sell_price`) * 100) desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `profit_1h`
--

/*!50001 DROP VIEW IF EXISTS `profit_1h`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8 */;
/*!50001 SET character_set_results     = utf8 */;
/*!50001 SET collation_connection      = utf8_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`%` SQL SECURITY DEFINER */
/*!50001 VIEW `profit_1h` AS select `trades_1h`.`buy_time` AS `buy_time`,`trades_1h`.`sell_time` AS `sell_time`,`trades_1h`.`pair` AS `pair`,`trades_1h`.`buy_price` AS `buy_price`,`trades_1h`.`sell_price` AS `sell_price`,`trades_1h`.`total` AS `total`,(((`trades_1h`.`sell_price` - `trades_1h`.`buy_price`) / `trades_1h`.`sell_price`) * 100) AS `perc`,(`trades_1h`.`sell_price` - `trades_1h`.`buy_price`) AS `base_profit`,(((`trades_1h`.`sell_price` - `trades_1h`.`buy_price`) * 8223.25) * `trades_1h`.`total`) AS `profit`,((`trades_1h`.`buy_price` * `trades_1h`.`total`) * 8223.25) AS `buy_bgp`,((`trades_1h`.`sell_price` * `trades_1h`.`total`) * 8223.25) AS `sell_gbp` from `trades_1h` order by (((`trades_1h`.`sell_price` - `trades_1h`.`buy_price`) / `trades_1h`.`sell_price`) * 100) desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `profit_1m`
--

/*!50001 DROP VIEW IF EXISTS `profit_1m`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8 */;
/*!50001 SET character_set_results     = utf8 */;
/*!50001 SET collation_connection      = utf8_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`%` SQL SECURITY DEFINER */
/*!50001 VIEW `profit_1m` AS select `trades_1m`.`buy_time` AS `buy_time`,`trades_1m`.`sell_time` AS `sell_time`,`trades_1m`.`pair` AS `pair`,`trades_1m`.`buy_price` AS `buy_price`,`trades_1m`.`sell_price` AS `sell_price`,`trades_1m`.`total` AS `total`,(((`trades_1m`.`sell_price` - `trades_1m`.`buy_price`) / `trades_1m`.`sell_price`) * 100) AS `perc`,(`trades_1m`.`sell_price` - `trades_1m`.`buy_price`) AS `base_profit`,(((`trades_1m`.`sell_price` - `trades_1m`.`buy_price`) * 8223.25) * `trades_1m`.`total`) AS `profit`,((`trades_1m`.`buy_price` * `trades_1m`.`total`) * 8223.25) AS `buy_bbp`,((`trades_1m`.`sell_price` * `trades_1m`.`total`) * 8223.25) AS `sell_gbp` from `trades_1m` order by (((`trades_1m`.`sell_price` - `trades_1m`.`buy_price`) / `trades_1m`.`sell_price`) * 100) desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `profit_3m`
--

/*!50001 DROP VIEW IF EXISTS `profit_3m`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8 */;
/*!50001 SET character_set_results     = utf8 */;
/*!50001 SET collation_connection      = utf8_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`%` SQL SECURITY DEFINER */
/*!50001 VIEW `profit_3m` AS select `trades_3m`.`buy_time` AS `buy_time`,`trades_3m`.`sell_time` AS `sell_time`,`trades_3m`.`pair` AS `pair`,`trades_3m`.`buy_price` AS `buy_price`,`trades_3m`.`sell_price` AS `sell_price`,`trades_3m`.`total` AS `total`,(((`trades_3m`.`sell_price` - `trades_3m`.`buy_price`) / `trades_3m`.`sell_price`) * 100) AS `perc`,(`trades_3m`.`sell_price` - `trades_3m`.`buy_price`) AS `base_profit`,(((`trades_3m`.`sell_price` - `trades_3m`.`buy_price`) * 8223.25) * `trades_3m`.`total`) AS `profit`,((`trades_3m`.`buy_price` * `trades_3m`.`total`) * 8223.25) AS `buy_bbp`,((`trades_3m`.`sell_price` * `trades_3m`.`total`) * 8223.25) AS `sell_gbp` from `trades_3m` order by (((`trades_3m`.`sell_price` - `trades_3m`.`buy_price`) / `trades_3m`.`sell_price`) * 100) desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `profit_5m`
--

/*!50001 DROP VIEW IF EXISTS `profit_5m`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8 */;
/*!50001 SET character_set_results     = utf8 */;
/*!50001 SET collation_connection      = utf8_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`%` SQL SECURITY DEFINER */
/*!50001 VIEW `profit_5m` AS select `trades_5m`.`buy_time` AS `buy_time`,`trades_5m`.`sell_time` AS `sell_time`,`trades_5m`.`pair` AS `pair`,`trades_5m`.`buy_price` AS `buy_price`,`trades_5m`.`sell_price` AS `sell_price`,`trades_5m`.`total` AS `total`,(((`trades_5m`.`sell_price` - `trades_5m`.`buy_price`) / `trades_5m`.`sell_price`) * 100) AS `perc`,(`trades_5m`.`sell_price` - `trades_5m`.`buy_price`) AS `base_profit`,(((`trades_5m`.`sell_price` - `trades_5m`.`buy_price`) * 8223.25) * `trades_5m`.`total`) AS `profit`,((`trades_5m`.`buy_price` * `trades_5m`.`total`) * 8223.25) AS `buy_bbp`,((`trades_5m`.`sell_price` * `trades_5m`.`total`) * 8223.25) AS `sell_gbp` from `trades_5m` order by (((`trades_5m`.`sell_price` - `trades_5m`.`buy_price`) / `trades_5m`.`sell_price`) * 100) desc */;
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

-- Dump completed on 2019-08-24 19:38:14
-- MySQL dump 10.13  Distrib 5.7.26, for Linux (x86_64)
--
-- Host: localhost    Database: greencandle
-- ------------------------------------------------------
-- Server version	5.7.26

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
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `exchange`
--

LOCK TABLES `exchange` WRITE;
/*!40000 ALTER TABLE `exchange` DISABLE KEYS */;
INSERT INTO `exchange` VALUES (3,'coinbase'),(4,'binance');
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

-- Dump completed on 2019-08-24 19:38:14
