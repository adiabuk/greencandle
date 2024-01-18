import sys
from greencandle.lib.auth import binance_auth
from greencandle.lib import config
from greencandle.lib.mysql import Mysql

config.create_config()
client = binance_auth()

usd_amount = dbase.get_var_value('max_trade_usd')
print(usd_amount, type(usd_amount))
sys.exit()
borrow_res = client.margin_borrow(symbol=pair, quantity=amount_to_borrow, isolated=False,
                                  asset=asset)
