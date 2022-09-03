# 4.2

# add binance order ids to trade
ALTER table trades ADD open_order_id int;
ALTER table trades ADD close_order_id int;
