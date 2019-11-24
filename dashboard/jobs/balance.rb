require 'mysql2'
current_balance = 0

SCHEDULER.every '10s' do

  db = Mysql2::Client.new(:host => "mysql", :username => "greencandle", :password => "password", :port => 3306, :database => "greencandle" )
  sql = "select round(sum(perc)/(datediff(max(sell_time),'2019-01-01 00:00')),2) as average from profit"


  balance_sql = "select round(gbp,2) from balance limit 1"
  balance = db.query(balance_sql)
  result = db.query(sql)
  last_balance = current_balance
  if balance.size == 0
    current_balance = 0
  else
    current_balance = balance.first['gbp']
  end
  puts result.first['average']
  send_event('balance', { current: current_balance, last: last_balance })
  send_event('synergy',   { value: result.first['average']*100 })
  db.close
end
