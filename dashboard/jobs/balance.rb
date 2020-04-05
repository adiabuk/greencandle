require 'mysql2'
current_balance = 0

SCHEDULER.every '30s' do
  puts "Getting balance..."
  db = Mysql2::Client.new(:host => "mysql", :username => "greencandle", :password => "password", :port => 3306, :database => "greencandle" )
  sql = "select round(sum(perc)/(datediff(max(sell_time),(select min(buy_time) from profit))),2) as average from profit"

  balance_spot_query = "select round(gbp,4) as gbp from balance where coin='TOTALS' and exchange_id=4 order by ctime desc limit 1"
  balance_spot = db.query(balance_spot_query)

  balance_margin_query = "select round(gbp,4) as gbp from balance where coin='TOTALS' and exchange_id=5 order by ctime desc limit 1"
  balance_margin = db.query(balance_margin_query)
  balance = balance_spot.first['gbp'].to_f + balance_margin.first['gbp'].to_f

  result = db.query(sql)
  last_balance = current_balance
  if balance == ""
    current_balance = 0
  else
    current_balance = balance
  end
  send_event('balance', { current: current_balance, last: last_balance })
  if result.size == 0
      value = 0
  else
      value = result.first['average'].to_f * 100
  end

  send_event('target',   { value: value })
  db.close
end
