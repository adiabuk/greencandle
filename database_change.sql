-- Version 2.17

UPDATE trades SET name = CONCAT('per-', name') WHERE close_price is null;

