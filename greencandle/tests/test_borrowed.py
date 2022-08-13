import unittest
import os
from unittest.mock import Mock
from unittest.mock import patch
from greencandle.lib import config
config.create_config()

from greencandle.lib.mysql import Mysql

from greencandle.lib.order import Trade



class TestBorrow(unittest.TestCase):

    def test_cross_long(self):
        os.system("configstore package process_templates unit/borrow/cross /etc")

        dbase=Mysql()
        mock = Mock()
        value = list((('WAVESUSDT', '1', 'short'), ('BCHUSDT', '1', 'short')))
        instance = mock.return_value
        instance.get_current_borrowed.return_value = value

        client = mock.return_value
        client.get_max_borrow.return_value=5000
        pair = "BTCUSDT"
        with patch('greencandle.lib.order.base2quote', return_value=10): #10 USD per item

            trade = Trade(interval='15m', test_data=False, test_trade=False, config=config)
            trade.client=client
            amt = trade.get_amount_to_borrow(pair, instance)

        self.assertEqual(config.main.trade_direction, "long")
        self.assertEqual(amt, (5000+20)/3)

    def test_cross_long2(self):
        """
        Change existing trades from short to long
        """
        os.system("configstore package process_templates unit/borrow/cross /etc")

        dbase=Mysql()
        mock = Mock()
        value = list((('WAVESUSDT', '1', 'long'), ('BCHUSDT', '1', 'long')))
        instance = mock.return_value
        instance.get_current_borrowed.return_value = value

        client = mock.return_value
        client.get_max_borrow.return_value=5000
        pair = "BTCUSDT"
        with patch('greencandle.lib.order.base2quote', return_value=10): #10 USD per item

            trade = Trade(interval='15m', test_data=False, test_trade=False, config=config)
            trade.client=client
            amt = trade.get_amount_to_borrow(pair, instance)

        self.assertEqual(config.main.trade_direction, "long")
        self.assertEqual(amt, (5000+2)/3)

    def test_cross_long3(self):
        """
        Change of existing traid quote, so quote2base is executed
        """
        os.system("configstore package process_templates unit/borrow/cross /etc")

        dbase=Mysql()
        mock = Mock()
        value = list((('WAVESETH', '1', 'long'), ('BCHBNB', '1', 'long')))
        instance = mock.return_value
        instance.get_current_borrowed.return_value = value

        client = mock.return_value
        client.get_max_borrow.return_value=5000
        pair = "BTCUSDT"
        with patch('greencandle.lib.order.base2quote', return_value=10): #10 USD per item

            trade = Trade(interval='15m', test_data=False, test_trade=False, config=config)
            trade.client=client
            amt = trade.get_amount_to_borrow(pair, instance)

        self.assertEqual(config.main.trade_direction, "long")
        self.assertEqual(amt, (5000+20)/3)

    def test_cross_long4(self):
        """
        Change of current pair, so quote changes to ETH
        """
        os.system("configstore package process_templates unit/borrow/cross /etc")

        dbase=Mysql()
        mock = Mock()
        value = list((('WAVESETH', '1', 'long'), ('BCHBNB', '1', 'long')))
        instance = mock.return_value
        instance.get_current_borrowed.return_value = value

        client = mock.return_value
        client.get_max_borrow.return_value=5000
        pair = "BNBETH"
        with patch('greencandle.lib.order.base2quote', return_value=10): #10 USD per item
            with patch('greencandle.lib.order.quote2base', return_value=20): #10 ETH

                trade = Trade(interval='15m', test_data=False, test_trade=False, config=config)
                trade.client=client
                amt = trade.get_amount_to_borrow(pair, instance)

        self.assertEqual(config.main.trade_direction, "long")
        self.assertEqual(amt, 20/3) # FIXME - this should be 5000 more


    def test_cross_long5(self):
        os.system("configstore package process_templates unit/borrow/cross/div /etc")

        dbase=Mysql()
        mock = Mock()
        value = list((('WAVESUSDT', '1', 'short'), ('BCHUSDT', '1', 'short')))
        instance = mock.return_value
        instance.get_current_borrowed.return_value = value

        client = mock.return_value
        client.get_max_borrow.return_value=5000
        pair = "BTCUSDT"
        with patch('greencandle.lib.order.base2quote', return_value=10): #10 USD per item

            trade = Trade(interval='15m', test_data=False, test_trade=False, config=config)
            trade.client=client
            amt = trade.get_amount_to_borrow(pair, instance)

        self.assertEqual(config.main.trade_direction, "long")
        self.assertEqual(amt, (5000+20)/10)


    def test_cross_short(self):
        os.system("configstore package process_templates unit/borrow/cross/short /etc")

        dbase=Mysql()
        mock = Mock()
        value = list((('WAVESUSDT', '1', 'long'), ('BCHUSDT', '1', 'short')))
        instance = mock.return_value
        instance.get_current_borrowed.return_value = value

        client = mock.return_value
        client.get_max_borrow.return_value=5000
        pair = "BTCUSDT"
        with patch('greencandle.lib.order.base2quote', return_value=10): #10 USD per item
            with patch('greencandle.lib.order.quote2base', return_value=20): #20 BTC

                trade = Trade(interval='15m', test_data=False, test_trade=False, config=config)
                trade.client=client
                amt = trade.get_amount_to_borrow(pair, instance)

        self.assertEqual(config.main.trade_direction, "short")
        self.assertEqual(amt, (20)/10)

    def test_isolated_long(self):
        os.system("configstore package process_templates unit/borrow/isolated /etc")

        dbase=Mysql()
        mock = Mock()
        value = list((('WAVESUSDT', '1', 'short'), ('BCHUSDT', '1', 'short')))
        instance = mock.return_value
        instance.get_current_borrowed.return_value = value

        client = mock.return_value
        client.get_max_borrow.return_value=5000
        pair = "BTCUSDT"
        with patch('greencandle.lib.order.base2quote', return_value=10): #10 USD per item

            trade = Trade(interval='15m', test_data=False, test_trade=False, config=config)
            trade.client=client
            amt = trade.get_amount_to_borrow(pair, instance)

        self.assertEqual(config.main.trade_direction, "long")
        self.assertEqual(amt, (5000+20)/3)

    def test_isolated_long2(self):
        """
        Change existing trades from short to long
        """
        os.system("configstore package process_templates unit/borrow/isolated /etc")

        dbase=Mysql()
        mock = Mock()
        value = list((('WAVESUSDT', '1', 'long'), ('BCHUSDT', '1', 'long')))
        instance = mock.return_value
        instance.get_current_borrowed.return_value = value

        client = mock.return_value
        client.get_max_borrow.return_value=5000
        pair = "BTCUSDT"
        with patch('greencandle.lib.order.base2quote', return_value=10): #10 USD per item

            trade = Trade(interval='15m', test_data=False, test_trade=False, config=config)
            trade.client=client
            amt = trade.get_amount_to_borrow(pair, instance)

        self.assertEqual(config.main.trade_direction, "long")
        self.assertEqual(amt, (5000+2)/3)

    def test_isolated_long3(self):
        """
        Change of existing traid quote, so quote2base is executed
        """
        os.system("configstore package process_templates unit/borrow/isolated /etc")

        dbase=Mysql()
        mock = Mock()
        value = list((('WAVESETH', '1', 'long'), ('BCHBNB', '1', 'long')))
        instance = mock.return_value
        instance.get_current_borrowed.return_value = value

        client = mock.return_value
        client.get_max_borrow.return_value=5000
        pair = "BTCUSDT"
        with patch('greencandle.lib.order.base2quote', return_value=10): #10 USD per item

            trade = Trade(interval='15m', test_data=False, test_trade=False, config=config)
            trade.client=client
            amt = trade.get_amount_to_borrow(pair, instance)

        self.assertEqual(config.main.trade_direction, "long")
        self.assertEqual(amt, (5000+20)/3)

    def test_isolated_long4(self):
        """
        Change of current pair, so quote changes to ETH
        """
        os.system("configstore package process_templates unit/borrow/isolated /etc")

        dbase=Mysql()
        mock = Mock()
        value = list((('WAVESETH', '1', 'long'), ('BCHBNB', '1', 'long')))
        instance = mock.return_value
        instance.get_current_borrowed.return_value = value

        client = mock.return_value
        client.get_max_borrow.return_value=5000
        pair = "BNBETH"
        with patch('greencandle.lib.order.base2quote', return_value=10): #10 USD per item
            with patch('greencandle.lib.order.quote2base', return_value=20): #10 ETH

                trade = Trade(interval='15m', test_data=False, test_trade=False, config=config)
                trade.client=client
                amt = trade.get_amount_to_borrow(pair, instance)

        self.assertEqual(config.main.trade_direction, "long")
        self.assertEqual(amt, (20)/3)


    def test_isolated_long5(self):
        os.system("configstore package process_templates unit/borrow/isolated/div /etc")

        dbase=Mysql()
        mock = Mock()
        value = list((('WAVESUSDT', '1', 'short'), ('BCHUSDT', '1', 'short')))
        instance = mock.return_value
        instance.get_current_borrowed.return_value = value

        client = mock.return_value
        client.get_max_borrow.return_value=5000
        pair = "BTCUSDT"
        with patch('greencandle.lib.order.base2quote', return_value=10): #10 USD per item

            trade = Trade(interval='15m', test_data=False, test_trade=False, config=config)
            trade.client=client
            amt = trade.get_amount_to_borrow(pair, instance)

        self.assertEqual(config.main.trade_direction, "long")
        self.assertEqual(amt, (5000+20)/10)


    def test_isolated_short(self):
        os.system("configstore package process_templates unit/borrow/isolated/short /etc")

        dbase=Mysql()
        mock = Mock()
        value = list((('WAVESUSDT', '1', 'long'), ('BCHUSDT', '1', 'short')))
        instance = mock.return_value
        instance.get_current_borrowed.return_value = value

        client = mock.return_value
        client.get_max_borrow.return_value=5000
        pair = "BTCUSDT"
        with patch('greencandle.lib.order.base2quote', return_value=10): #10 USD per item
            with patch('greencandle.lib.order.quote2base', return_value=20): #20 BTC

                trade = Trade(interval='15m', test_data=False, test_trade=False, config=config)
                trade.client=client
                amt = trade.get_amount_to_borrow(pair, instance)

        self.assertEqual(config.main.trade_direction, "short")
        self.assertEqual(amt, (20)/10)

