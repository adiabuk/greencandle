use greencandle;

ALTER TABLE trades ADD COLUMN direction varchar(30)
update trades set direction="long" where direction="";
drop view profit;

CREATE VIEW profit as select `trades`.`open_time` AS `open_time`,`trades`.`interval` AS `interval`,`trades`.`close_time` AS `close_time`,`trades`.`pair` AS `pair`,`trades`.`open_price` AS `open_price`,`trades`.`close_price` AS `close_price`,
CASE
            WHEN direction = "long" THEN (((`trades`.`close_price` - `trades`.`open_price`) / `trades`.`open_price`) * 100)
            ELSE (((`trades`.`open_price` - `trades`.`close_price`) / `trades`.`open_price`) * 100)
        END perc,

CASE
           WHEN direction = "long" THEN (`trades`.`base_out` - `trades`.`base_in`)
          ELSE (`trades`.`base_in` - `trades`.`base_out`)
          END base_profit,


,`trades`.`drawdown_perc` AS `drawdown_perc` from `trades`;



DROP VIEW daily_profit;
CREATE VIEW daily_profit as  select left(`profit`.`close_time`,10) AS `date`,sum(`profit`.`base_profit`) AS `profit`,sum(`profit`.`perc`) AS `perc` from `profit` where (`profit`.`perc` is not null) group by left(`profit`.`close_time`,10) order by left(`profit`.`close_time`,10),sum(`profit`.`base_profit`);
