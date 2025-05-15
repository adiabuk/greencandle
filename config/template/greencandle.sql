-- MariaDB dump 10.19  Distrib 10.8.3-MariaDB, for debian-linux-gnu (x86_64)
--
-- Host: 127.1    Database: greencandle
-- ------------------------------------------------------
-- Server version	10.8.3-MariaDB-1:10.8.3+maria~jammy

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
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
/*!50001 CREATE TABLE `accounts` (
  `open_time` tinyint NOT NULL,
  `close_time` tinyint NOT NULL,
  `open_price` tinyint NOT NULL,
  `close_price` tinyint NOT NULL,
  `perc` tinyint NOT NULL,
  `borrowed` tinyint NOT NULL,
  `profit` tinyint NOT NULL,
  `pair` tinyint NOT NULL,
  `quote_pair` tinyint NOT NULL,
  `name` tinyint NOT NULL,
  `quote_out` tinyint NOT NULL,
  `quote_in` tinyint NOT NULL,
  `amount` tinyint NOT NULL
) ENGINE=MyISAM */;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `accounts2`
--

DROP TABLE IF EXISTS `accounts2`;
/*!50001 DROP VIEW IF EXISTS `accounts2`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE TABLE `accounts2` (
  `id` tinyint NOT NULL,
  `open_time` tinyint NOT NULL,
  `close_time` tinyint NOT NULL,
  `pair` tinyint NOT NULL,
  `gross_profit_perc` tinyint NOT NULL,
  `net_profit_perc` tinyint NOT NULL,
  `usd_gross_profit` tinyint NOT NULL,
  `gbp_gross_profit` tinyint NOT NULL,
  `usd_net_profit` tinyint NOT NULL,
  `gbp_net_profit` tinyint NOT NULL
) ENGINE=MyISAM */;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `api_requests`
--

DROP TABLE IF EXISTS `api_requests`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `api_requests` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `date` datetime DEFAULT current_timestamp(),
  `pair` varchar(30) DEFAULT NULL,
  `text` varchar(100) DEFAULT NULL,
  `action` varchar(30) DEFAULT NULL,
  `price` varchar(30) DEFAULT NULL,
  `strategy` varchar(30) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `balance`
--

DROP TABLE IF EXISTS `balance`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `balance` (
  `id` int(11) unsigned NOT NULL AUTO_INCREMENT,
  `ctime` timestamp NULL DEFAULT current_timestamp(),
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
  `ctime` timestamp NULL DEFAULT current_timestamp(),
  `usd` double DEFAULT NULL,
  `btc` varchar(30) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `commission_paid`
--

DROP TABLE IF EXISTS `commission_paid`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `commission_paid` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `date` datetime DEFAULT current_timestamp(),
  `asset` varchar(30) DEFAULT NULL,
  `asset_amt` varchar(30) NOT NULL,
  `usd_amt` decimal(15,2) NOT NULL,
  `gbp_amt` decimal(15,2) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Temporary table structure for view `commission_paid_daily`
--

DROP TABLE IF EXISTS `commission_paid_daily`;
/*!50001 DROP VIEW IF EXISTS `commission_paid_daily`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE TABLE `commission_paid_daily` (
  `sum(gbp_amt)` tinyint NOT NULL,
  `date` tinyint NOT NULL
) ENGINE=MyISAM */;
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
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `extra_loans`
--

DROP TABLE IF EXISTS `extra_loans`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `extra_loans` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `symbol` varchar(6) DEFAULT NULL,
  `date_added` datetime DEFAULT current_timestamp(),
  `date_removed` datetime DEFAULT NULL,
  `borrowed` varchar(30) DEFAULT '0',
  `borrowed_usd` varchar(30) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Temporary table structure for view `profit`
--

DROP TABLE IF EXISTS `profit`;
/*!50001 DROP VIEW IF EXISTS `profit`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE TABLE `profit` (
  `id` tinyint NOT NULL,
  `day` tinyint NOT NULL,
  `open_time` tinyint NOT NULL,
  `interval` tinyint NOT NULL,
  `close_time` tinyint NOT NULL,
  `pair` tinyint NOT NULL,
  `name` tinyint NOT NULL,
  `open_price` tinyint NOT NULL,
  `close_price` tinyint NOT NULL,
  `perc` tinyint NOT NULL,
  `net_perc` tinyint NOT NULL,
  `quote_profit` tinyint NOT NULL,
  `quote_net_profit` tinyint NOT NULL,
  `usd_profit` tinyint NOT NULL,
  `usd_net_profit` tinyint NOT NULL,
  `quote_in` tinyint NOT NULL,
  `quote_out` tinyint NOT NULL,
  `base_in` tinyint NOT NULL,
  `base_out` tinyint NOT NULL,
  `drawup_perc` tinyint NOT NULL,
  `drawdown_perc` tinyint NOT NULL,
  `borrowed` tinyint NOT NULL,
  `borrowed_usd` tinyint NOT NULL,
  `divisor` tinyint NOT NULL,
  `direction` tinyint NOT NULL,
  `open_usd_rate` tinyint NOT NULL,
  `close_usd_rate` tinyint NOT NULL,
  `open_gbp_rate` tinyint NOT NULL,
  `close_gbp_rate` tinyint NOT NULL,
  `comm_open` tinyint NOT NULL,
  `comm_close` tinyint NOT NULL,
  `comment` tinyint NOT NULL
) ENGINE=MyISAM */;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `profit_by_dayname_direction`
--

DROP TABLE IF EXISTS `profit_by_dayname_direction`;
/*!50001 DROP VIEW IF EXISTS `profit_by_dayname_direction`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE TABLE `profit_by_dayname_direction` (
  `day_name` tinyint NOT NULL,
  `net_perc` tinyint NOT NULL,
  `direction` tinyint NOT NULL,
  `net_perc_profitable` tinyint NOT NULL
) ENGINE=MyISAM */;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `profit_by_direction`
--

DROP TABLE IF EXISTS `profit_by_direction`;
/*!50001 DROP VIEW IF EXISTS `profit_by_direction`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE TABLE `profit_by_direction` (
  `day` tinyint NOT NULL,
  `net_perc` tinyint NOT NULL,
  `direction` tinyint NOT NULL,
  `net_perc_profitable` tinyint NOT NULL
) ENGINE=MyISAM */;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `profit_by_direction_hour_close`
--

DROP TABLE IF EXISTS `profit_by_direction_hour_close`;
/*!50001 DROP VIEW IF EXISTS `profit_by_direction_hour_close`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE TABLE `profit_by_direction_hour_close` (
  `day` tinyint NOT NULL,
  `hour` tinyint NOT NULL,
  `net_perc` tinyint NOT NULL,
  `count` tinyint NOT NULL,
  `name` tinyint NOT NULL,
  `direction` tinyint NOT NULL,
  `net_perc_profitable` tinyint NOT NULL
) ENGINE=MyISAM */;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `profit_by_direction_hour_open`
--

DROP TABLE IF EXISTS `profit_by_direction_hour_open`;
/*!50001 DROP VIEW IF EXISTS `profit_by_direction_hour_open`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE TABLE `profit_by_direction_hour_open` (
  `day` tinyint NOT NULL,
  `hour` tinyint NOT NULL,
  `net_perc` tinyint NOT NULL,
  `count` tinyint NOT NULL,
  `name` tinyint NOT NULL,
  `direction` tinyint NOT NULL,
  `net_perc_profitable` tinyint NOT NULL
) ENGINE=MyISAM */;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `profit_daily_breakdown_close`
--

DROP TABLE IF EXISTS `profit_daily_breakdown_close`;
/*!50001 DROP VIEW IF EXISTS `profit_daily_breakdown_close`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE TABLE `profit_daily_breakdown_close` (
  `dayname` tinyint NOT NULL,
  `interval` tinyint NOT NULL,
  `close_date` tinyint NOT NULL,
  `name` tinyint NOT NULL,
  `count` tinyint NOT NULL,
  `net_perc` tinyint NOT NULL,
  `direction` tinyint NOT NULL,
  `perc_profitable` tinyint NOT NULL,
  `net_perc_profitable` tinyint NOT NULL
) ENGINE=MyISAM */;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `profit_daily_breakdown_open`
--

DROP TABLE IF EXISTS `profit_daily_breakdown_open`;
/*!50001 DROP VIEW IF EXISTS `profit_daily_breakdown_open`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE TABLE `profit_daily_breakdown_open` (
  `dayname` tinyint NOT NULL,
  `interval` tinyint NOT NULL,
  `close_date` tinyint NOT NULL,
  `name` tinyint NOT NULL,
  `count` tinyint NOT NULL,
  `net_perc` tinyint NOT NULL,
  `direction` tinyint NOT NULL,
  `perc_profitable` tinyint NOT NULL,
  `net_perc_profitable` tinyint NOT NULL
) ENGINE=MyISAM */;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `profit_daily_by_close`
--

DROP TABLE IF EXISTS `profit_daily_by_close`;
/*!50001 DROP VIEW IF EXISTS `profit_daily_by_close`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE TABLE `profit_daily_by_close` (
  `date` tinyint NOT NULL,
  `day` tinyint NOT NULL,
  `sum_net_perc` tinyint NOT NULL,
  `avg_net_perc` tinyint NOT NULL,
  `max_net_perc` tinyint NOT NULL,
  `min_net_perc` tinyint NOT NULL,
  `count` tinyint NOT NULL,
  `net_loss` tinyint NOT NULL,
  `perc_profitable` tinyint NOT NULL,
  `net_perc_profitable` tinyint NOT NULL,
  `usd_net_profit` tinyint NOT NULL
) ENGINE=MyISAM */;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `profit_daily_by_open`
--

DROP TABLE IF EXISTS `profit_daily_by_open`;
/*!50001 DROP VIEW IF EXISTS `profit_daily_by_open`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE TABLE `profit_daily_by_open` (
  `date` tinyint NOT NULL,
  `day` tinyint NOT NULL,
  `sum_net_perc` tinyint NOT NULL,
  `avg_net_perc` tinyint NOT NULL,
  `max_net_perc` tinyint NOT NULL,
  `min_net_perc` tinyint NOT NULL,
  `count` tinyint NOT NULL,
  `net_loss` tinyint NOT NULL,
  `perc_profitable` tinyint NOT NULL,
  `net_perc_profitable` tinyint NOT NULL,
  `usd_net_profit` tinyint NOT NULL
) ENGINE=MyISAM */;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `profit_hourly`
--

DROP TABLE IF EXISTS `profit_hourly`;
/*!50001 DROP VIEW IF EXISTS `profit_hourly`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE TABLE `profit_hourly` (
  `date` tinyint NOT NULL,
  `day` tinyint NOT NULL,
  `hour` tinyint NOT NULL,
  `total_perc` tinyint NOT NULL,
  `total_net_perc` tinyint NOT NULL,
  `avg_perc` tinyint NOT NULL,
  `avg_net_perc` tinyint NOT NULL,
  `usd_profit` tinyint NOT NULL,
  `usd_net_profit` tinyint NOT NULL,
  `num_trades` tinyint NOT NULL
) ENGINE=MyISAM */;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `profit_monthly`
--

DROP TABLE IF EXISTS `profit_monthly`;
/*!50001 DROP VIEW IF EXISTS `profit_monthly`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE TABLE `profit_monthly` (
  `date` tinyint NOT NULL,
  `usd_profit` tinyint NOT NULL,
  `usd_net_profit` tinyint NOT NULL,
  `perc` tinyint NOT NULL,
  `net_perc` tinyint NOT NULL,
  `count` tinyint NOT NULL
) ENGINE=MyISAM */;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `profit_weekly`
--

DROP TABLE IF EXISTS `profit_weekly`;
/*!50001 DROP VIEW IF EXISTS `profit_weekly`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE TABLE `profit_weekly` (
  `week_no` tinyint NOT NULL,
  `week_commencing` tinyint NOT NULL,
  `count` tinyint NOT NULL,
  `usd_profit` tinyint NOT NULL,
  `usd_net_profit` tinyint NOT NULL,
  `perc` tinyint NOT NULL,
  `net_perc` tinyint NOT NULL
) ENGINE=MyISAM */;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `profitable_all`
--

DROP TABLE IF EXISTS `profitable_all`;
/*!50001 DROP VIEW IF EXISTS `profitable_all`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE TABLE `profitable_all` (
  `pair` tinyint NOT NULL,
  `name` tinyint NOT NULL,
  `total` tinyint NOT NULL,
  `profit` tinyint NOT NULL,
  `net_profit` tinyint NOT NULL,
  `loss` tinyint NOT NULL,
  `net_loss` tinyint NOT NULL,
  `perc_profitable` tinyint NOT NULL,
  `net_perc_profitable` tinyint NOT NULL,
  `perc` tinyint NOT NULL,
  `per_trade` tinyint NOT NULL,
  `net_perc` tinyint NOT NULL,
  `net_per_trade` tinyint NOT NULL,
  `max(perc)` tinyint NOT NULL,
  `min(perc)` tinyint NOT NULL,
  `max(net_perc)` tinyint NOT NULL,
  `min(net_perc)` tinyint NOT NULL
) ENGINE=MyISAM */;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `profitable_by_name`
--

DROP TABLE IF EXISTS `profitable_by_name`;
/*!50001 DROP VIEW IF EXISTS `profitable_by_name`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE TABLE `profitable_by_name` (
  `name` tinyint NOT NULL,
  `total` tinyint NOT NULL,
  `profit` tinyint NOT NULL,
  `net_profit` tinyint NOT NULL,
  `net_loss` tinyint NOT NULL,
  `perc_profitable` tinyint NOT NULL,
  `net_perc_profitable` tinyint NOT NULL,
  `total_perc` tinyint NOT NULL,
  `per_trade` tinyint NOT NULL,
  `total_net_perc` tinyint NOT NULL,
  `net_per_trade` tinyint NOT NULL,
  `max(perc)` tinyint NOT NULL,
  `min(perc)` tinyint NOT NULL,
  `max(net_perc)` tinyint NOT NULL,
  `min(net_perc)` tinyint NOT NULL
) ENGINE=MyISAM */;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `profitable_by_name_date`
--

DROP TABLE IF EXISTS `profitable_by_name_date`;
/*!50001 DROP VIEW IF EXISTS `profitable_by_name_date`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE TABLE `profitable_by_name_date` (
  `name` tinyint NOT NULL,
  `direction` tinyint NOT NULL,
  `date` tinyint NOT NULL,
  `total` tinyint NOT NULL,
  `profit` tinyint NOT NULL,
  `net_profit` tinyint NOT NULL,
  `net_loss` tinyint NOT NULL,
  `perc_profitable` tinyint NOT NULL,
  `net_perc_profitable` tinyint NOT NULL,
  `total_perc` tinyint NOT NULL,
  `per_trade` tinyint NOT NULL,
  `total_net_perc` tinyint NOT NULL,
  `net_per_trade` tinyint NOT NULL,
  `max(perc)` tinyint NOT NULL,
  `min(perc)` tinyint NOT NULL,
  `max(net_perc)` tinyint NOT NULL,
  `min(net_perc)` tinyint NOT NULL
) ENGINE=MyISAM */;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `profitable_by_name_direction`
--

DROP TABLE IF EXISTS `profitable_by_name_direction`;
/*!50001 DROP VIEW IF EXISTS `profitable_by_name_direction`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE TABLE `profitable_by_name_direction` (
  `name` tinyint NOT NULL,
  `direction` tinyint NOT NULL,
  `total` tinyint NOT NULL,
  `profit` tinyint NOT NULL,
  `net_profit` tinyint NOT NULL,
  `net_loss` tinyint NOT NULL,
  `perc_profitable` tinyint NOT NULL,
  `net_perc_profitable` tinyint NOT NULL,
  `total_perc` tinyint NOT NULL,
  `per_trade` tinyint NOT NULL,
  `total_net_perc` tinyint NOT NULL,
  `net_per_trade` tinyint NOT NULL,
  `max(perc)` tinyint NOT NULL,
  `min(perc)` tinyint NOT NULL,
  `max(net_perc)` tinyint NOT NULL,
  `min(net_perc)` tinyint NOT NULL
) ENGINE=MyISAM */;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `profitable_hours`
--

DROP TABLE IF EXISTS `profitable_hours`;
/*!50001 DROP VIEW IF EXISTS `profitable_hours`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8;
/*!50001 CREATE TABLE `profitable_hours` (
  `hour` tinyint NOT NULL,
  `hour_perc` tinyint NOT NULL,
  `net_hour_perc` tinyint NOT NULL,
  `total_count` tinyint NOT NULL,
  `num_profit` tinyint NOT NULL,
  `net_num_profit` tinyint NOT NULL,
  `num_loss` tinyint NOT NULL,
  `net_num_loss` tinyint NOT NULL
) ENGINE=MyISAM */;
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
  `pair` varchar(15) DEFAULT NULL,
  `interval` varchar(3) DEFAULT NULL,
  `open_price` varchar(30) DEFAULT NULL,
  `close_price` varchar(30) DEFAULT NULL,
  `base_in` varchar(40) DEFAULT NULL,
  `base_out` varchar(40) DEFAULT NULL,
  `quote_in` varchar(40) DEFAULT NULL,
  `quote_out` varchar(40) DEFAULT NULL,
  `name` varchar(40) DEFAULT NULL,
  `closed_by` varchar(40) DEFAULT NULL,
  `drawdown_perc` varchar(6) DEFAULT NULL,
  `borrowed` varchar(30) DEFAULT '0',
  `borrowed_usd` varchar(30) DEFAULT NULL,
  `divisor` varchar(3) DEFAULT '0',
  `direction` varchar(30) DEFAULT NULL,
  `drawup_perc` varchar(6) DEFAULT NULL,
  `open_usd_rate` varchar(30) DEFAULT NULL,
  `open_gbp_rate` varchar(30) DEFAULT NULL,
  `close_usd_rate` varchar(30) DEFAULT NULL,
  `close_gbp_rate` varchar(30) DEFAULT NULL,
  `comm_open` varchar(255) DEFAULT NULL,
  `comm_close` varchar(255) DEFAULT NULL,
  `open_order_id` varchar(30) DEFAULT NULL,
  `close_order_id` varchar(30) DEFAULT NULL,
  `comment` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `variables`
--

DROP TABLE IF EXISTS `variables`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `variables` (
  `name` varchar(30) DEFAULT NULL,
  `value` varchar(30) DEFAULT NULL,
  UNIQUE KEY `name` (`name`),
  UNIQUE KEY `name_2` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping routines for database 'greencandle'
--
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
/*!50003 DROP FUNCTION IF EXISTS `ADD_PERCENT` */;
ALTER DATABASE `greencandle` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`%` FUNCTION `ADD_PERCENT`(amount DOUBLE,perc decimal(10,2)) RETURNS double
RETURN IF(amount > 0, amount + (amount*perc/100), amount - (amount*perc/100)) ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
ALTER DATABASE `greencandle` CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
/*!50003 DROP FUNCTION IF EXISTS `commission` */;
ALTER DATABASE `greencandle` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`%` FUNCTION `commission`() RETURNS decimal(10,2)
RETURN (select value from variables where name='commission' LIMIT 1) ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
ALTER DATABASE `greencandle` CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
/*!50003 DROP FUNCTION IF EXISTS `FIRST_DAY_OF_WEEK` */;
ALTER DATABASE `greencandle` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb3 */ ;
/*!50003 SET character_set_results = utf8mb3 */ ;
/*!50003 SET collation_connection  = utf8mb3_general_ci */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`%` FUNCTION `FIRST_DAY_OF_WEEK`(day DATE) RETURNS date
    DETERMINISTIC
BEGIN
  RETURN SUBDATE(day, WEEKDAY(day));
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
ALTER DATABASE `greencandle` CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
/*!50003 DROP FUNCTION IF EXISTS `get_var` */;
ALTER DATABASE `greencandle` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`%` FUNCTION `get_var`(`name_in` VARCHAR(30)) RETURNS varchar(30) CHARSET utf8mb4
RETURN (select value from variables where `name`=name_in LIMIT 1) ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
ALTER DATABASE `greencandle` CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
/*!50003 DROP FUNCTION IF EXISTS `PERC_DIFF` */;
ALTER DATABASE `greencandle` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`%` FUNCTION `PERC_DIFF`(direction varchar(30),
money_in varchar(30),
money_out varchar(30)
) RETURNS decimal(10,6)
RETURN

CASE WHEN money_out = 0 or money_in=0
   THEN NULL
ELSE
 IF(direction = "long", (money_out-money_in)/money_in *100,  (money_in-money_out)/money_in *100 )
 END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
ALTER DATABASE `greencandle` CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
/*!50003 DROP FUNCTION IF EXISTS `REMOVE_PERCENT` */;
ALTER DATABASE `greencandle` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`%` FUNCTION `REMOVE_PERCENT`(amount varchar(30),perc varchar(30)) RETURNS varchar(30) CHARSET latin1
RETURN IF(amount > 0, amount - (amount*perc/100), amount + (amount*perc/100)) ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
ALTER DATABASE `greencandle` CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
/*!50003 DROP FUNCTION IF EXISTS `REOPEN_TRADE` */;
ALTER DATABASE `greencandle` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`%` FUNCTION `REOPEN_TRADE`(reopen_id int(11)) RETURNS int(11)
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
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
ALTER DATABASE `greencandle` CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
/*!50003 DROP PROCEDURE IF EXISTS `GetProfitableByDayName` */;
ALTER DATABASE `greencandle` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb3 */ ;
/*!50003 SET character_set_results = utf8mb3 */ ;
/*!50003 SET collation_connection  = utf8mb3_general_ci */ ;
DELIMITER ;;
CREATE DEFINER=`root`@`%` PROCEDURE `GetProfitableByDayName`(
	IN dayname VARCHAR(255), intervalx VARCHAR(255)
)
BEGIN
	SELECT name, sum(net_perc), direction, count(*)
 	FROM profit_daily_breakdown
	WHERE dayname = dayname and `interval` = intervalx
	group by name, direction
	order by sum(net_perc) desc;
END ;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
ALTER DATABASE `greencandle` CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci ;

--
-- Final view structure for view `accounts`
--

/*!50001 DROP TABLE IF EXISTS `accounts`*/;
/*!50001 DROP VIEW IF EXISTS `accounts`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`%` SQL SECURITY DEFINER */
/*!50001 VIEW `accounts` AS select `p`.`open_time` AS `open_time`,`t`.`close_time` AS `close_time`,`t`.`open_price` AS `open_price`,`t`.`close_price` AS `close_price`,`p`.`perc` AS `perc`,`t`.`borrowed` AS `borrowed`,`p`.`quote_profit` AS `profit`,`t`.`pair` AS `pair`,case when `t`.`pair` like '%BTC' then 'BTC' when `t`.`pair` like '%BNB' then 'BNB' when `t`.`pair` like '%ETH' then 'ETH' when `t`.`pair` like '%USDT' then 'USDT' end AS `quote_pair`,`t`.`name` AS `name`,`t`.`base_out` AS `quote_out`,`t`.`base_in` AS `quote_in`,`t`.`quote_in` AS `amount` from (`trades` `t` join `profit` `p`) where `p`.`id` = `t`.`id` and `t`.`close_price` is not null */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `accounts2`
--

/*!50001 DROP TABLE IF EXISTS `accounts2`*/;
/*!50001 DROP VIEW IF EXISTS `accounts2`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`%` SQL SECURITY DEFINER */
/*!50001 VIEW `accounts2` AS select `profit`.`id` AS `id`,`profit`.`open_time` AS `open_time`,`profit`.`close_time` AS `close_time`,`profit`.`pair` AS `pair`,`profit`.`perc` AS `gross_profit_perc`,`profit`.`net_perc` AS `net_profit_perc`,case when `profit`.`direction` = 'long' then (`profit`.`quote_out` - `profit`.`quote_in`) * `profit`.`close_usd_rate` else (`profit`.`quote_in` - `profit`.`quote_out`) * `profit`.`close_usd_rate` end AS `usd_gross_profit`,case when `profit`.`direction` = 'long' then (`profit`.`quote_out` - `profit`.`quote_in`) * `profit`.`close_gbp_rate` else (`profit`.`quote_in` - `profit`.`quote_out`) * `profit`.`close_gbp_rate` end AS `gbp_gross_profit`,case when `profit`.`direction` = 'long' then (`profit`.`quote_out` - `add_percent`(`profit`.`quote_in`,`commission`())) * `profit`.`close_usd_rate` else (`remove_percent`(`profit`.`quote_in`,`commission`()) - `profit`.`quote_out`) * `profit`.`close_usd_rate` end AS `usd_net_profit`,case when `profit`.`direction` = 'long' then (`profit`.`quote_out` - `add_percent`(`profit`.`quote_in`,`commission`())) * `profit`.`close_gbp_rate` else (`remove_percent`(`profit`.`quote_in`,`commission`()) - `profit`.`quote_out`) * `profit`.`close_gbp_rate` end AS `gbp_net_profit` from `profit` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `commission_paid_daily`
--

/*!50001 DROP TABLE IF EXISTS `commission_paid_daily`*/;
/*!50001 DROP VIEW IF EXISTS `commission_paid_daily`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`%` SQL SECURITY DEFINER */
/*!50001 VIEW `commission_paid_daily` AS select sum(`commission_paid`.`gbp_amt`) AS `sum(gbp_amt)`,cast(`commission_paid`.`date` as date) AS `date` from `commission_paid` group by cast(`commission_paid`.`date` as date) desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `profit`
--

/*!50001 DROP TABLE IF EXISTS `profit`*/;
/*!50001 DROP VIEW IF EXISTS `profit`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`%` SQL SECURITY DEFINER */
/*!50001 VIEW `profit` AS select `trades`.`id` AS `id`,dayname(`trades`.`open_time`) AS `day`,`trades`.`open_time` AS `open_time`,`trades`.`interval` AS `interval`,`trades`.`close_time` AS `close_time`,`trades`.`pair` AS `pair`,`trades`.`name` AS `name`,`trades`.`open_price` AS `open_price`,`trades`.`close_price` AS `close_price`,cast(`PERC_DIFF`(`trades`.`direction`,`trades`.`open_price`,`trades`.`close_price`) as decimal(12,4)) AS `perc`,cast(`PERC_DIFF`(`trades`.`direction`,`trades`.`open_price`,`trades`.`close_price`) - `commission`() as decimal(12,4)) AS `net_perc`,case when `trades`.`direction` = 'long' then `trades`.`quote_out` - `trades`.`quote_in` else `trades`.`quote_in` - `trades`.`quote_out` end AS `quote_profit`,case when `trades`.`direction` = 'long' then `trades`.`quote_out` - `add_percent`(`trades`.`quote_in`,`commission`()) else `remove_percent`(`trades`.`quote_in`,`commission`()) - `trades`.`quote_out` end AS `quote_net_profit`,case when `trades`.`direction` = 'long' then (`trades`.`quote_out` - `trades`.`quote_in`) * `trades`.`close_usd_rate` else (`trades`.`quote_in` - `trades`.`quote_out`) * `trades`.`close_usd_rate` end AS `usd_profit`,case when `trades`.`direction` = 'long' then (`trades`.`quote_out` - `add_percent`(`trades`.`quote_in`,`commission`())) * `trades`.`close_usd_rate` else (`remove_percent`(`trades`.`quote_in`,`commission`()) - `trades`.`quote_out`) * `trades`.`close_usd_rate` end AS `usd_net_profit`,`trades`.`quote_in` AS `quote_in`,`trades`.`quote_out` AS `quote_out`,`trades`.`base_in` AS `base_in`,`trades`.`base_out` AS `base_out`,`trades`.`drawup_perc` AS `drawup_perc`,`trades`.`drawdown_perc` AS `drawdown_perc`,`trades`.`borrowed` AS `borrowed`,`trades`.`borrowed_usd` AS `borrowed_usd`,`trades`.`divisor` AS `divisor`,`trades`.`direction` AS `direction`,`trades`.`open_usd_rate` AS `open_usd_rate`,`trades`.`close_usd_rate` AS `close_usd_rate`,`trades`.`open_gbp_rate` AS `open_gbp_rate`,`trades`.`close_gbp_rate` AS `close_gbp_rate`,`trades`.`comm_open` AS `comm_open`,`trades`.`comm_close` AS `comm_close`,`trades`.`comment` AS `comment` from `trades` where `trades`.`close_price` is not null and `trades`.`close_price` <> '' and `trades`.`name` like (select `get_var`('filter')) order by `trades`.`close_time` desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `profit_by_dayname_direction`
--

/*!50001 DROP TABLE IF EXISTS `profit_by_dayname_direction`*/;
/*!50001 DROP VIEW IF EXISTS `profit_by_dayname_direction`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb3 */;
/*!50001 SET character_set_results     = utf8mb3 */;
/*!50001 SET collation_connection      = utf8mb3_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`%` SQL SECURITY DEFINER */
/*!50001 VIEW `profit_by_dayname_direction` AS select dayname(`profit`.`open_time`) AS `day_name`,sum(`profit`.`net_perc`) AS `net_perc`,`profit`.`direction` AS `direction`,sum(case when `profit`.`net_perc` > 0 then 1 else 0 end) / count(0) * 100 AS `net_perc_profitable` from `profit` group by dayname(`profit`.`open_time`),`profit`.`direction` order by field(`profit`.`day`,'Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday') */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `profit_by_direction`
--

/*!50001 DROP TABLE IF EXISTS `profit_by_direction`*/;
/*!50001 DROP VIEW IF EXISTS `profit_by_direction`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`%` SQL SECURITY DEFINER */
/*!50001 VIEW `profit_by_direction` AS select cast(`profit`.`open_time` as date) AS `day`,sum(`profit`.`net_perc`) AS `net_perc`,`profit`.`direction` AS `direction`,sum(case when `profit`.`net_perc` > 0 then 1 else 0 end) / count(0) * 100 AS `net_perc_profitable` from `profit` group by cast(`profit`.`open_time` as date),`profit`.`direction` order by cast(`profit`.`open_time` as date) desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `profit_by_direction_hour_close`
--

/*!50001 DROP TABLE IF EXISTS `profit_by_direction_hour_close`*/;
/*!50001 DROP VIEW IF EXISTS `profit_by_direction_hour_close`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb3 */;
/*!50001 SET character_set_results     = utf8mb3 */;
/*!50001 SET collation_connection      = utf8mb3_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`%` SQL SECURITY DEFINER */
/*!50001 VIEW `profit_by_direction_hour_close` AS select cast(`profit`.`close_time` as date) AS `day`,hour(`profit`.`close_time`) AS `hour`,sum(`profit`.`net_perc`) AS `net_perc`,count(0) AS `count`,`profit`.`name` AS `name`,`profit`.`direction` AS `direction`,sum(case when `profit`.`net_perc` > 0 then 1 else 0 end) / count(0) * 100 AS `net_perc_profitable` from `profit` group by cast(`profit`.`close_time` as date),`profit`.`direction`,`profit`.`name`,hour(`profit`.`close_time`) order by cast(`profit`.`close_time` as date) desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `profit_by_direction_hour_open`
--

/*!50001 DROP TABLE IF EXISTS `profit_by_direction_hour_open`*/;
/*!50001 DROP VIEW IF EXISTS `profit_by_direction_hour_open`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb3 */;
/*!50001 SET character_set_results     = utf8mb3 */;
/*!50001 SET collation_connection      = utf8mb3_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`%` SQL SECURITY DEFINER */
/*!50001 VIEW `profit_by_direction_hour_open` AS select cast(`profit`.`open_time` as date) AS `day`,hour(`profit`.`open_time`) AS `hour`,sum(`profit`.`net_perc`) AS `net_perc`,count(0) AS `count`,`profit`.`name` AS `name`,`profit`.`direction` AS `direction`,sum(case when `profit`.`net_perc` > 0 then 1 else 0 end) / count(0) * 100 AS `net_perc_profitable` from `profit` group by cast(`profit`.`open_time` as date),`profit`.`direction`,`profit`.`name`,hour(`profit`.`open_time`) order by cast(`profit`.`open_time` as date) desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `profit_daily_breakdown_close`
--

/*!50001 DROP TABLE IF EXISTS `profit_daily_breakdown_close`*/;
/*!50001 DROP VIEW IF EXISTS `profit_daily_breakdown_close`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb3 */;
/*!50001 SET character_set_results     = utf8mb3 */;
/*!50001 SET collation_connection      = utf8mb3_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`%` SQL SECURITY DEFINER */
/*!50001 VIEW `profit_daily_breakdown_close` AS select dayname(`profit`.`close_time`) AS `dayname`,`profit`.`interval` AS `interval`,cast(`profit`.`close_time` as date) AS `close_date`,`profit`.`name` AS `name`,count(0) AS `count`,sum(`profit`.`net_perc`) AS `net_perc`,`profit`.`direction` AS `direction`,sum(case when `profit`.`perc` > 0 then 1 else 0 end) / count(0) * 100 AS `perc_profitable`,sum(case when `profit`.`net_perc` > 0 then 1 else 0 end) / count(0) * 100 AS `net_perc_profitable` from `profit` group by `profit`.`name`,`profit`.`direction`,cast(`profit`.`close_time` as date) order by cast(`profit`.`close_time` as date) desc,sum(`profit`.`net_perc`) desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `profit_daily_breakdown_open`
--

/*!50001 DROP TABLE IF EXISTS `profit_daily_breakdown_open`*/;
/*!50001 DROP VIEW IF EXISTS `profit_daily_breakdown_open`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb3 */;
/*!50001 SET character_set_results     = utf8mb3 */;
/*!50001 SET collation_connection      = utf8mb3_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`%` SQL SECURITY DEFINER */
/*!50001 VIEW `profit_daily_breakdown_open` AS select dayname(`profit`.`open_time`) AS `dayname`,`profit`.`interval` AS `interval`,cast(`profit`.`open_time` as date) AS `close_date`,`profit`.`name` AS `name`,count(0) AS `count`,sum(`profit`.`net_perc`) AS `net_perc`,`profit`.`direction` AS `direction`,sum(case when `profit`.`perc` > 0 then 1 else 0 end) / count(0) * 100 AS `perc_profitable`,sum(case when `profit`.`net_perc` > 0 then 1 else 0 end) / count(0) * 100 AS `net_perc_profitable` from `profit` group by `profit`.`name`,`profit`.`direction`,cast(`profit`.`open_time` as date) order by cast(`profit`.`open_time` as date) desc,sum(`profit`.`net_perc`) desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `profit_daily_by_close`
--

/*!50001 DROP TABLE IF EXISTS `profit_daily_by_close`*/;
/*!50001 DROP VIEW IF EXISTS `profit_daily_by_close`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`%` SQL SECURITY DEFINER */
/*!50001 VIEW `profit_daily_by_close` AS select cast(`profit`.`close_time` as date) AS `date`,dayname(`profit`.`close_time`) AS `day`,sum(cast(`profit`.`net_perc` as decimal(12,2))) AS `sum_net_perc`,avg(cast(`profit`.`net_perc` as decimal(12,2))) AS `avg_net_perc`,max(cast(`profit`.`net_perc` as decimal(12,2))) AS `max_net_perc`,min(cast(`profit`.`net_perc` as decimal(12,2))) AS `min_net_perc`,count(0) AS `count`,sum(case when `profit`.`net_perc` < 0 then 1 else 0 end) AS `net_loss`,sum(case when `profit`.`net_perc` > 0 then 1 else 0 end) / count(0) * 100 AS `perc_profitable`,sum(case when `profit`.`net_perc` > 0 then 1 else 0 end) / count(0) * 100 AS `net_perc_profitable`,sum(cast(`profit`.`usd_net_profit` as decimal(12,2))) AS `usd_net_profit` from `profit` group by cast(`profit`.`close_time` as date) order by cast(`profit`.`close_time` as date) desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `profit_daily_by_open`
--

/*!50001 DROP TABLE IF EXISTS `profit_daily_by_open`*/;
/*!50001 DROP VIEW IF EXISTS `profit_daily_by_open`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`%` SQL SECURITY DEFINER */
/*!50001 VIEW `profit_daily_by_open` AS select cast(`profit`.`open_time` as date) AS `date`,dayname(`profit`.`open_time`) AS `day`,sum(cast(`profit`.`net_perc` as decimal(12,2))) AS `sum_net_perc`,avg(cast(`profit`.`net_perc` as decimal(12,2))) AS `avg_net_perc`,max(cast(`profit`.`net_perc` as decimal(12,2))) AS `max_net_perc`,min(cast(`profit`.`net_perc` as decimal(12,2))) AS `min_net_perc`,count(0) AS `count`,sum(case when `profit`.`net_perc` < 0 then 1 else 0 end) AS `net_loss`,sum(case when `profit`.`net_perc` > 0 then 1 else 0 end) / count(0) * 100 AS `perc_profitable`,sum(case when `profit`.`net_perc` > 0 then 1 else 0 end) / count(0) * 100 AS `net_perc_profitable`,sum(cast(`profit`.`usd_net_profit` as decimal(12,2))) AS `usd_net_profit` from `profit` group by cast(`profit`.`open_time` as date) order by cast(`profit`.`open_time` as date) desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `profit_hourly`
--

/*!50001 DROP TABLE IF EXISTS `profit_hourly`*/;
/*!50001 DROP VIEW IF EXISTS `profit_hourly`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`%` SQL SECURITY DEFINER */
/*!50001 VIEW `profit_hourly` AS select date_format(`profit`.`close_time`,'%Y-%m-%d') AS `date`,dayname(`profit`.`close_time`) AS `day`,date_format(`profit`.`close_time`,'%H') AS `hour`,sum(`profit`.`perc`) AS `total_perc`,sum(`profit`.`net_perc`) AS `total_net_perc`,avg(`profit`.`perc`) AS `avg_perc`,avg(`profit`.`net_perc`) AS `avg_net_perc`,sum(`profit`.`usd_profit`) AS `usd_profit`,sum(`profit`.`usd_net_profit`) AS `usd_net_profit`,count(0) AS `num_trades` from `profit` where year(`profit`.`close_time`) <> 0 group by hour(`profit`.`close_time`),dayofmonth(`profit`.`close_time`),month(`profit`.`close_time`),year(`profit`.`close_time`) order by `profit`.`close_time` desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `profit_monthly`
--

/*!50001 DROP TABLE IF EXISTS `profit_monthly`*/;
/*!50001 DROP VIEW IF EXISTS `profit_monthly`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`%` SQL SECURITY DEFINER */
/*!50001 VIEW `profit_monthly` AS select left(`profit`.`close_time`,7) AS `date`,sum(`profit`.`usd_profit`) AS `usd_profit`,sum(`profit`.`usd_net_profit`) AS `usd_net_profit`,sum(`profit`.`perc`) AS `perc`,sum(`profit`.`net_perc`) AS `net_perc`,count(0) AS `count` from `profit` where `profit`.`perc` is not null and year(`profit`.`close_time`) <> '0000' group by left(`profit`.`close_time`,7) order by left(`profit`.`close_time`,7) desc,sum(`profit`.`quote_profit`) */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `profit_weekly`
--

/*!50001 DROP TABLE IF EXISTS `profit_weekly`*/;
/*!50001 DROP VIEW IF EXISTS `profit_weekly`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`%` SQL SECURITY DEFINER */
/*!50001 VIEW `profit_weekly` AS select concat(year(`profit`.`close_time`),'/',week(`profit`.`close_time`)) AS `week_no`,`FIRST_DAY_OF_WEEK`(cast(`profit`.`close_time` as date)) AS `week_commencing`,count(0) AS `count`,sum(`profit`.`usd_profit`) AS `usd_profit`,sum(`profit`.`usd_net_profit`) AS `usd_net_profit`,sum(`profit`.`perc`) AS `perc`,sum(`profit`.`net_perc`) AS `net_perc` from `profit` where week(`profit`.`close_time`) is not null group by concat(year(`profit`.`close_time`),'/',week(`profit`.`close_time`)) order by year(`profit`.`close_time`) desc,week(`profit`.`close_time`) desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `profitable_all`
--

/*!50001 DROP TABLE IF EXISTS `profitable_all`*/;
/*!50001 DROP VIEW IF EXISTS `profitable_all`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`%` SQL SECURITY DEFINER */
/*!50001 VIEW `profitable_all` AS select `profit`.`pair` AS `pair`,`profit`.`name` AS `name`,count(0) AS `total`,sum(case when `profit`.`perc` > 0 then 1 else 0 end) AS `profit`,sum(case when `profit`.`net_perc` > 0 then 1 else 0 end) AS `net_profit`,sum(case when `profit`.`perc` < 0 then 1 else 0 end) AS `loss`,sum(case when `profit`.`net_perc` < 0 then 1 else 0 end) AS `net_loss`,sum(case when `profit`.`perc` > 0 then 1 else 0 end) / count(0) * 100 AS `perc_profitable`,sum(case when `profit`.`net_perc` > 0 then 1 else 0 end) / count(0) * 100 AS `net_perc_profitable`,sum(`profit`.`perc`) AS `perc`,sum(`profit`.`perc`) / count(0) AS `per_trade`,sum(`profit`.`net_perc`) AS `net_perc`,sum(`profit`.`net_perc`) / count(0) AS `net_per_trade`,max(`profit`.`perc`) AS `max(perc)`,min(`profit`.`perc`) AS `min(perc)`,max(`profit`.`net_perc`) AS `max(net_perc)`,min(`profit`.`net_perc`) AS `min(net_perc)` from `profit` where `profit`.`pair` is not null group by `profit`.`pair`,`profit`.`name` order by sum(case when `profit`.`perc` > 0 then 1 else 0 end) / count(0) * 100 desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `profitable_by_name`
--

/*!50001 DROP TABLE IF EXISTS `profitable_by_name`*/;
/*!50001 DROP VIEW IF EXISTS `profitable_by_name`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`%` SQL SECURITY DEFINER */
/*!50001 VIEW `profitable_by_name` AS select `profit`.`name` AS `name`,count(0) AS `total`,sum(case when `profit`.`perc` > 0 then 1 else 0 end) AS `profit`,sum(case when `profit`.`net_perc` > 0 then 1 else 0 end) AS `net_profit`,sum(case when `profit`.`net_perc` < 0 then 1 else 0 end) AS `net_loss`,sum(case when `profit`.`perc` > 0 then 1 else 0 end) / count(0) * 100 AS `perc_profitable`,sum(case when `profit`.`net_perc` > 0 then 1 else 0 end) / count(0) * 100 AS `net_perc_profitable`,sum(`profit`.`perc`) AS `total_perc`,sum(`profit`.`perc`) / count(0) AS `per_trade`,sum(`profit`.`net_perc`) AS `total_net_perc`,sum(`profit`.`net_perc`) / count(0) AS `net_per_trade`,max(`profit`.`perc`) AS `max(perc)`,min(`profit`.`perc`) AS `min(perc)`,max(`profit`.`net_perc`) AS `max(net_perc)`,min(`profit`.`net_perc`) AS `min(net_perc)` from `profit` group by `profit`.`name` order by sum(case when `profit`.`perc` > 0 then 1 else 0 end) / count(0) * 100 desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `profitable_by_name_date`
--

/*!50001 DROP TABLE IF EXISTS `profitable_by_name_date`*/;
/*!50001 DROP VIEW IF EXISTS `profitable_by_name_date`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`%` SQL SECURITY DEFINER */
/*!50001 VIEW `profitable_by_name_date` AS select `profit`.`name` AS `name`,`profit`.`direction` AS `direction`,cast(`profit`.`close_time` as date) AS `date`,count(0) AS `total`,sum(case when `profit`.`perc` > 0 then 1 else 0 end) AS `profit`,sum(case when `profit`.`net_perc` > 0 then 1 else 0 end) AS `net_profit`,sum(case when `profit`.`net_perc` < 0 then 1 else 0 end) AS `net_loss`,sum(case when `profit`.`perc` > 0 then 1 else 0 end) / count(0) * 100 AS `perc_profitable`,sum(case when `profit`.`net_perc` > 0 then 1 else 0 end) / count(0) * 100 AS `net_perc_profitable`,sum(`profit`.`perc`) AS `total_perc`,sum(`profit`.`perc`) / count(0) AS `per_trade`,sum(`profit`.`net_perc`) AS `total_net_perc`,sum(`profit`.`net_perc`) / count(0) AS `net_per_trade`,max(`profit`.`perc`) AS `max(perc)`,min(`profit`.`perc`) AS `min(perc)`,max(`profit`.`net_perc`) AS `max(net_perc)`,min(`profit`.`net_perc`) AS `min(net_perc)` from `profit` group by `profit`.`name`,cast(`profit`.`close_time` as date),`profit`.`direction` order by cast(`profit`.`open_time` as date) desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `profitable_by_name_direction`
--

/*!50001 DROP TABLE IF EXISTS `profitable_by_name_direction`*/;
/*!50001 DROP VIEW IF EXISTS `profitable_by_name_direction`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb3 */;
/*!50001 SET character_set_results     = utf8mb3 */;
/*!50001 SET collation_connection      = utf8mb3_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`%` SQL SECURITY DEFINER */
/*!50001 VIEW `profitable_by_name_direction` AS select `profit`.`name` AS `name`,`profit`.`direction` AS `direction`,count(0) AS `total`,sum(case when `profit`.`perc` > 0 then 1 else 0 end) AS `profit`,sum(case when `profit`.`net_perc` > 0 then 1 else 0 end) AS `net_profit`,sum(case when `profit`.`net_perc` < 0 then 1 else 0 end) AS `net_loss`,sum(case when `profit`.`perc` > 0 then 1 else 0 end) / count(0) * 100 AS `perc_profitable`,sum(case when `profit`.`net_perc` > 0 then 1 else 0 end) / count(0) * 100 AS `net_perc_profitable`,sum(`profit`.`perc`) AS `total_perc`,sum(`profit`.`perc`) / count(0) AS `per_trade`,sum(`profit`.`net_perc`) AS `total_net_perc`,sum(`profit`.`net_perc`) / count(0) AS `net_per_trade`,max(`profit`.`perc`) AS `max(perc)`,min(`profit`.`perc`) AS `min(perc)`,max(`profit`.`net_perc`) AS `max(net_perc)`,min(`profit`.`net_perc`) AS `min(net_perc)` from `profit` group by `profit`.`name`,`profit`.`direction` order by sum(`profit`.`perc`) desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `profitable_hours`
--

/*!50001 DROP TABLE IF EXISTS `profitable_hours`*/;
/*!50001 DROP VIEW IF EXISTS `profitable_hours`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`%` SQL SECURITY DEFINER */
/*!50001 VIEW `profitable_hours` AS select `profit_hourly`.`hour` AS `hour`,sum(`profit_hourly`.`total_perc`) AS `hour_perc`,sum(`profit_hourly`.`total_net_perc`) AS `net_hour_perc`,count(0) AS `total_count`,sum(case when `profit_hourly`.`total_perc` > 0 then 1 else 0 end) AS `num_profit`,sum(case when `profit_hourly`.`total_net_perc` > 0 then 1 else 0 end) AS `net_num_profit`,sum(case when `profit_hourly`.`total_perc` < 0 then 1 else 0 end) AS `num_loss`,sum(case when `profit_hourly`.`total_net_perc` < 0 then 1 else 0 end) AS `net_num_loss` from `profit_hourly` group by `profit_hourly`.`hour` */;
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

-- Dump completed on 2025-05-15 18:05:04
-- MariaDB dump 10.19  Distrib 10.8.3-MariaDB, for debian-linux-gnu (x86_64)
--
-- Host: 127.1    Database: greencandle
-- ------------------------------------------------------
-- Server version	10.8.3-MariaDB-1:10.8.3+maria~jammy

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `variables`
--

DROP TABLE IF EXISTS `variables`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `variables` (
  `name` varchar(30) DEFAULT NULL,
  `value` varchar(30) DEFAULT NULL,
  UNIQUE KEY `name` (`name`),
  UNIQUE KEY `name_2` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `variables`
--

LOCK TABLES `variables` WRITE;
/*!40000 ALTER TABLE `variables` DISABLE KEYS */;
INSERT INTO `variables` VALUES
('commission','0.15'),
('start_time','01:30'),
('end_time','08:30'),
('max_trade_usd','5500'),
('filter','%%'),
('max_trades','1000');
/*!40000 ALTER TABLE `variables` ENABLE KEYS */;
UNLOCK TABLES;

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
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `exchange`
--

LOCK TABLES `exchange` WRITE;
/*!40000 ALTER TABLE `exchange` DISABLE KEYS */;
INSERT INTO `exchange` VALUES
(3,'coinbase'),
(4,'binance'),
(5,'margin'),
(6,'phemex'),
(7,'isolated');
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

-- Dump completed on 2025-05-15 18:05:04
