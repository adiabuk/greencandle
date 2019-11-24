
require 'mysql2'
db = Mysql2::Client.new(:host => "mysql", :username => "greencandle", :password => "password", :port => 3306, :database => "greencandle" )

query = "select pair, round(buy_price,4) as buy_price, buy_time, round(current_price,4) as current_price, round(perc,2) as perc from open_trades"
results = db.query(query)
print results
hrows = [
 { cols: [ {value: 'pair'}, {value: 'buy_time'}, {value: 'buy_price'}, {value: 'current_price'}, {value: 'perc'}]}
]
table = Array.new
results.each do |row|
table.push({ cols: [ {value: row['pair']}, {value: row['buy_time']}, {value: row['buy_price']},{value: row['current_price']},{value: row['perc']} ]})
end
send_event('my-table', { hrows: hrows, rows: table })
