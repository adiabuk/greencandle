use greencandle;

alter table trades add drawup_perc varchar(4);

drop view profit;

CREATE VIEW profit as select `trades`.`open_time` AS `open_time`,`trades`.`interval` AS `interval`,`trades`.`close_time` AS `close_time`,`trades`.`pair` AS `pair`,`trades`.`open_price` AS `open_price`,`trades`.`close_price` AS `close_price`,
CASE
            WHEN direction = "long" THEN (((`trades`.`close_price` - `trades`.`open_price`) / `trades`.`open_price`) * 100)
            ELSE (((`trades`.`open_price` - `trades`.`close_price`) / `trades`.`open_price`) * 100)
        END perc,

CASE
           WHEN direction = "long" THEN (`trades`.`base_out` - `trades`.`base_in`)
          ELSE (`trades`.`base_in` - `trades`.`base_out`)
          END base_profit


,`trades`.`drawdown_perc` AS `drawdown_perc`, `trades`.`drawup_perc` as `drawup_perc` from `trades`;
