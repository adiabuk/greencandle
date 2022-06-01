-- Version 3.8

create view profitable_hours as select hour, sum(total_perc) as hour_perc, count(*) as total_count, sum((case when (`total_perc` > 0) then 1 else 0 end)) as num_profit,
sum((case when (`total_perc` < 0) then 1 else 0 end)) as num_loss from hourly_profit group by hour;
