#!/usr/bin/env python
"""
split exisiting open trade using new trade value and interval/name
"""
import sys
from greencandle.lib.mysql import Mysql
from greencandle.lib.common import perc_diff, sub_perc, arg_decorator

def get_query(data_dict):
    """
    Create insert query given a dictionary of keys (columns) and values
    """
    query_head = "insert into trades "
    keys = ",".join([f"`{x}`" for x in data_dict.keys()])
    values = ",".join([f"\"{x}\"" for x in data_dict.values()])
    return f"{query_head} ({keys}) VALUES ({values})"

@arg_decorator
def main():
    """
    Split open_trade for a given database id
    given inputs of name, interval and quote amount.
    * First trade will use exisiting name with reduced amount
    * Second trade will use leftover amount and new name
    * Original trade will be deleted
    """
    old_id = input('Enter id of db record you want to split: ')
    new_name = input('Enter new name: ')
    new_interval = input('Enter new interval: ')
    new_quote_in = input('Enter quote amount: ')


    dbase = Mysql()
    trades = dbase.fetch_sql_data(f"select * from trades where id={old_id}")

    data = dict(zip(trades[0], trades[1]))
    diff = perc_diff(data['quote_in'], new_quote_in)
    # first = old name + reduced amount
    # second = new_name + leftover amount

    second_base_in = sub_perc(abs(diff), data['base_in'])
    second_quote_in = sub_perc(abs(diff), data['quote_in'])

    first_base_in = float(data['base_in']) - second_base_in
    first_quote_in = float(data['quote_in']) - second_quote_in

    new1 = {k: v for k, v in data.items() if v is not None}
    new1.pop('id', None)
    new2 = new1.copy()

    new1['base_in'] = first_base_in
    new1['quote_in'] = first_quote_in

    new2['base_in'] = second_base_in
    new2['quote_in'] = second_quote_in
    new2['name'] = new_name
    new2['interval'] = new_interval

    query1 = get_query(new1)
    query2 = get_query(new2)
    delete_query = f'delete from trades where id = {old_id}'

    print('\n')
    print("Original")
    print(f"pair: {data['pair']}, id: {data['id']}, name: {data['name']}, interval: "
          f"{data['interval']}")
    print(f"base_in: {data['base_in']}, quote_in: {data['quote_in']}")
    print('\n')
    print("first record:")
    print(f"base_in: {first_base_in}, quote_in: {first_quote_in}, name: {data['name']}, "
          f"{data['interval']}")
    print('\n')
    print("second record:")
    print(f"base_in: {second_base_in}, quote_in: {second_quote_in}, name: {new_name}, "
          f"interval: {new_interval}")
    print('\n')
    proceed = input('Would you like to proceed?(y/n) ').lower()
    if proceed == 'y':
        print("Queries to run:")
        print(query1)
        print(query2)
        print(delete_query)
        dbase.run_sql_statement(query1)
        dbase.run_sql_statement(query2)
        #dbase.run_sql_statement(delete_query)
    else:
        print('exiting')
        sys.exit()

if __name__ == '__main__':
    main()
