#pylint: disable=no-member,unused-variable,broad-except,eval-used
"""
Mudule to evaluate sentiment for config in given context
To be used in trading environments only
"""
from greencandle.lib.web import get_prom_value
from greencandle.lib import config
from greencandle.lib.objects import AttributeDict
from greencandle.lib.logger import get_logger

config.create_config()

class Sentiment(dict):
    """
    Fetch and evaluate sentiment in given context
    """
    def __init__(self):
        """
        Fetch TV values specified in config
        """
        self.logger = get_logger(self.__class__.__name__)
        results = {}
        indicators = config.main.indicators.split()
        if "None" in indicators:
            self.res = AttributeDict()
        else:
            for ind in indicators:
                method, name, interval = ind.split(';')
                results[f'{name}_{interval}'] = float(eval(f'self.{method}("{interval}")'))

            self.res = AttributeDict(results)

    @staticmethod
    def get_tv(interval):
        """
        Get tv value from prometheus for given interval
        """
        result = get_prom_value(f'last_over_time(tv_all_value_{interval}[10m])')
        return result

    @staticmethod
    def get_ema(interval):
        """
        Get EMA Sentiment from prometheus - minimum value over last 5 hrs
        """
        query_str = 'up' if config.main.trade_direction == 'long' else 'down'
        result = get_prom_value(f'min_over_time(EMA_150_{query_str}_{interval}[1h])')
        return result

    @staticmethod
    def get_hl_dir(interval):
        """
        Get HL direction from prometheus aggregate

        """
        try:
            up = int(get_prom_value(f'data_HL_up_{interval}'))
            down = int(get_prom_value(f'data_HL_down_{interval}'))
        except (ValueError, KeyError):
            return "unknown"

        return "up" if up > down else "down"


    def get_results(self):
        """
        Evaluate results for given config, using prefetched values
        """
        res = self.res
        rules = []
        for seq in range(1, 6):
            try:
                current_config = config.main[f'open_rule{seq}']
            except (KeyError, TypeError):
                self.logger.info("Unable to fetch rule %s", seq)
            if current_config:
                try:
                    rules.append(eval(current_config))
                except Exception:
                    self.logger.info("Unable to eval rule %s", seq)
        self.logger.info("Matched Rules: %s",rules)
        return any(rules)
