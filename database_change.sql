# 4.8

# for test:
update trades set name='test-be-eng-bbpercst-short' where name='test-be-eng-bbperc-short';
update trades set name='test-be-eng-bbpercst-long' where name='test-be-eng-bbperc-long';
update open_trades set name='test-be-eng-bbpercst-short' where name='test-be-eng-bbperc-short';
update open_trades set name='test-be-eng-bbpercst-long' where name='test-be-eng-bbperc-long';
UPDATE trades SET name = REPLACE(field, 'test', 'stag') WHERE INSTR(field, 'test') > 0;
UPDATE open_trades SET name = REPLACE(field, 'test', 'stag') WHERE INSTR(field, 'test') > 0;

# for stag:
update trades set name='any-test-short' where name='test-any-short';
update trades set name='any-test-long' where name='test-any-long';
update open_trades set name='any-test-short' where name='test-any-short';
update open_trades set name='any-test-long' where name='test-any-long';
update trades set name='test-be-eng-bbpercorig-short' where name='test-be-eng-bbperc-short';
update trades set name='test-be-eng-bbpercorig-long' where name='test-be-eng-bbperc-long';
update open_trades set name='test-be-eng-bbpercorig-short' where name='test-be-eng-bbperc-short';
update open_trades set name='test-be-eng-bbpercorig-long' where name='test-be-eng-bbperc-long';
