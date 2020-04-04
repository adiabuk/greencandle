require 'mysql2'
current_balance = 0

SCHEDULER.every '30s' do
  puts "Getting balance..."
  db = Mysql2::Client.new(:host => "mysql", :username => "greencandle", :password => "password", :port => 3306, :database => "greencandle" )
  sql = "select round(sum(perc)/(datediff(max(sell_time),(select min(buy_time) from profit))),2) as average from profit"

  balance_spot_query = "select round(gbp,2) as gbp from balance where coin='TOTALS' and exchange_id=4 order by ctime desc limit 1"
  balance_spot = db.query(balance_spot_query)

  balance_margin_query = "select round(gbp,2) as gbp from balance where coin='TOTALS' and exchange_id=5 order by ctime desc limit 1"
  balance_margin = db.query(balance_spot_query)
  balance = balance_spot.to_f + balance_margin.to_f

  result = db.query(sql)
  last_balance = current_balance
  if balance.size == 0
    current_balance = 0
  else
    current_balance = balance.first['gbp']
  end
  send_event('balance', { current: current_balance, last: last_balance })
  send_event('target',   { value: result.first['average']*100 })
  db.close
end
