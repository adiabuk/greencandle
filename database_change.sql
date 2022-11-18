# 5.3

drop function if exists get_var;
CREATE FUNCTION `get_var`(`name_in` VARCHAR(30)) RETURNS varchar(30) CHARSET utf8mb4
RETURN (select value from variables where `name`=name_in LIMIT 1)
