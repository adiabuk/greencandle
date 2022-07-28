-- Version 3.25

drop function if exists REMOVE_PERCENT;
CREATE FUNCTION `REMOVE_PERCENT`(amount decimal(10,2),perc decimal(10,2)) RETURNS decimal(10,2)
RETURN IF(amount > 0, amount - (amount*perc/100), amount + (amount*perc/100));
