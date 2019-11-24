# Get Current and previous perc from profit table for plotting graph
require 'mysql2'

points = []


sql = "select truncate(perc,2) as perc from profit where sell_time != '0000-00-00 00:00:00' order by sell_time desc limit 1"
db = Mysql2::Client.new(:host => "mysql", :username => "greencandle", :password => "password", :port => 3306, :database => "greencandle" )

(1..10).each do |i|
  points << { x: i, y: rand(50) }
end
last_x = points.last[:x]



SCHEDULER.every '10s' do
  points.shift
  last_x += 1
  result = db.query(sql)
  if not result.first.nil?
    points << { x: last_x, y: result.first['perc'] }
    send_event('convergence', points: points)
    last_x = points.last[:x]
  end

end
