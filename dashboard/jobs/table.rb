
require 'mysql2'


SCHEDULER.every '120s', :first_in => 0 do |job|
    puts "Getting current open trades..."
    db = Mysql2::Client.new(:host => "mysql", :username => "greencandle", :password => "password", :port => 3306, :database => "greencandle" )

    query = "select pair, round(open_price,5) as open_price, open_time, round(current_price,5) as current_price, round(perc,2) as perc from open_trades order by perc"
    results = db.query(query)
    print results
    hrows = [
     { cols: [ {value: 'pair'}, {value: 'open_time'}, {value: 'open_price'}, {value: 'current_price'}, {value: 'perc'}]}
    ]
    table = Array.new
    results.each do |row|
        table.push({ cols: [ {value: row['pair']}, {value: row['open_time']}, {value: row['open_price']},{value: row['current_price']},{value: row['perc']} ]})
    end
    send_event('my-table', { hrows: hrows, rows: table })
    db.close
end
