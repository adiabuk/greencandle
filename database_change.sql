-- Version 3.7

create view hourly_profit as select date_format(close_time, '%Y-%m-%d') as date, DATE_FORMAT(close_time,'%H') as hour, sum(perc) as total_perc, avg(perc) as avg_perc, sum(usd_profit) as usd_profit, count(*) as num_trades   from profit where year(close_time) !=0 group by hour(close_time), day(close_time), month(close_time), year(close_time) order by close_time desc;
select IFNULL((select usd_profit from hourly_profit where date='2022-05-30' and hour=13), 0);

drop view hour_balance;
