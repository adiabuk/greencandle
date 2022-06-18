-- Version 3.18

drop table if exists open_trades;
drop view if exists open_trades;
create view open_trades as select pair, open_time, open_price, name, `interval`, 
                                     open_usd_rate*quote_in as usd_quantity from 
                                     trades where close_price is NULL or close_price=''
                                     ;

