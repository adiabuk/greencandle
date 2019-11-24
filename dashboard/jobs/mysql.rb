# Get top6 and bottom6 trades by pair pair

require 'mysql2'

SCHEDULER.every '15s', :first_in => 0 do |job|

  # Myql connection
  db = Mysql2::Client.new(:host => "mysql", :username => "greencandle", :password => "password", :port => 3306, :database => "greencandle" )

  # Mysql query

  ascending = "SELECT pair, concat(truncate(sum(perc),2),'%') as perc from profit where sell_time != '0000-00-00 00:00:00' group by pair order by sum(perc) asc limit 6"

  descending = "SELECT pair, concat(truncate(sum(perc),2),'%') as perc from profit where sell_time != '0000-00-00 00:00:00' group by pair order by sum(perc) desc limit 6"

  # Execute the query
  ascending_results = db.query(ascending)
  descending_results = db.query(descending)

  # Sending to List widget, so map to :label and :value
  asc = ascending_results.map do |row|
    row = {
      :label => row['pair'],
      :value => row['perc']
    }
  end

  desc = descending_results.map do |row|
    row = {
      :label => row['pair'],
      :value => row['perc']
    }
  end

  # Update the List widget
  send_event('asc1', { items: asc } )
  send_event('desc1', { items: desc } )

  db.close
end
