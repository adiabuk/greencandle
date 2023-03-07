# 5.18

CREATE or replace FUNCTION `PERC_DIFF`(direction varchar(30),
money_in varchar(30),
money_out varchar(30)
) RETURNS varchar(30) CHARSET utf8mb4
RETURN

CASE WHEN money_out = 0 or money_in=0
   THEN NULL
ELSE
 IF(direction = "long", (money_out-money_in)/money_in *100,  (money_in-money_out)/money_in *100 )
 END;
