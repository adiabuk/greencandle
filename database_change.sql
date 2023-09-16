# 6.39

# Fix character set
SET collation_connection = 'utf8_general_ci';
ALTER DATABASE greencandle CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE trades CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;
