require 'mysql2'
current_valuation = 0
current_karma = 0

SCHEDULER.every '10s' do

  db = Mysql2::Client.new(:host => "127.0.0.1", :username => "root", :password => "password", :port => 3306, :database => "greencandle_test" )
  sql = "select round(sum(perc)/(datediff(max(sell_time),'2018-01-01 00:00')),2) as average from profit"


  balance_sql = "select gbp from balance limit 1"
  balance = db.query(balance_sql)
  result = db.query(sql)
  last_valuation = current_valuation
  last_karma     = current_karma
  current_valuation = balance.first['gbp']
  current_karma     = rand(200000)
  puts result.first['average']
  send_event('valuation', { current: current_valuation, last: last_valuation })
  send_event('karma', { current: current_karma, last: last_karma })
  send_event('synergy',   { value: result.first['average']*100 })
end
