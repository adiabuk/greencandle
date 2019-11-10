require 'mysql2'

SCHEDULER.every '15s', :first_in => 0 do |job|

  # Myql connection
  db = Mysql2::Client.new(:host => "mysql", :username => "root", :password => "password", :port => 3306, :database => "greencandle" )

  # Mysql query
  #sql = "SELECT acct AS account, COUNT( acct ) AS count FROM users ORDER BY COUNT(*) DESC LIMIT 0 , 5"
  sql1 = "SELECT pair, concat(truncate(sum(perc),2),'%') as perc from profit where sell_time != '0000-00-00 00:00:00' group by pair order by sum(perc) asc limit 6"
  sql2 = "SELECT pair, concat(truncate(sum(perc),2),'%') as perc from profit where sell_time != '0000-00-00 00:00:00' group by pair order by sum(perc) desc limit 6"
  # Execute the query
  results1 = db.query(sql1)
  results2 = db.query(sql2)

  # Sending to List widget, so map to :label and :value
  asc = results1.map do |row|
    row = {
      :label => row['pair'],
      :value => row['perc']
    }
  end
  desc = results2.map do |row|
    row = {
      :label => row['pair'],
      :value => row['perc']
    }

  end

  # Update the List widget
  send_event('asc1', { items: asc } )
  send_event('desc1', { items: desc } )

end

