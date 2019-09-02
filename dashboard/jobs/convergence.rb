# Populate the graph with some random points
require 'mysql2'

points = []
(1..10).each do |i|
  points << { x: i, y: rand(50) }
end
last_x = points.last[:x]

sql = "select truncate(perc,2) as perc from profit where sell_time != '0000-00-00 00:00:00' order by sell_time desc limit 1"
db = Mysql2::Client.new(:host => "mysql", :username => "root", :password => "password", :port => 3306, :database => "greencandle_test" )
SCHEDULER.every '10s' do
  points.shift
  last_x += 1
  result = db.query(sql)
  points << { x: last_x, y: result.first['perc'] }

  send_event('convergence', points: points)
end
