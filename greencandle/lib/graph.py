#pylint: disable=no-member,logging-not-lazy
"""Create candlestick graphs from OHLC data"""

import ast
import time
import datetime
import pickle
import zlib
from collections import defaultdict
import pandas
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from pyvirtualdisplay import Display

import plotly.offline as py
import plotly.graph_objs as go
from plotly import subplots

from PIL import Image
from resizeimage import resizeimage
from . import config
from .redis_conn import Redis

from .logger import get_logger

LOGGER = get_logger(__name__)

class Graph():
    """class for creating graph html and images"""
    def __init__(self, test=False, pair='ETHBTC', interval='1m', volume=True):
        self.test = test
        self.pair = pair
        self.interval = interval
        self.data = {}
        self.filename = ''
        self.volume = volume

    def get_screenshot(self, output_dir=''):
        """Capture screenshot using selenium/firefox in Xvfb """
        display = Display(visible=0, size=(1366, 768))
        display.start()
        cap = DesiredCapabilities().FIREFOX
        cap["marionette"] = True
        profile = webdriver.FirefoxProfile()
        profile.set_preference("browser.download.folderList", 2)  # custom location
        profile.set_preference("browser.download.manager.showWhenStarting", False)
        profile.set_preference("browser.download.dir", "/tmp")
        profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "image/png")

        driver = webdriver.Firefox(firefox_profile=profile, capabilities=cap,
                                   executable_path="/usr/local/bin/geckodriver")
        driver.get("file://{0}/{1}".format(output_dir, self.filename))
        driver.save_screenshot("{0}/{1}.png".format(output_dir, self.filename))
        time.sleep(10)
        driver.quit()
        display.stop()

    def resize_screenshot(self, output_dir=''):
        """Resize screenshot to thumbnail - for use in API"""
        with open("{0}/{1}.png".format(output_dir, self.filename), "r+b") as png_file:
            with Image.open(png_file) as image:
                _, height = image.size

                # Setting the points for cropped image
                left = 90
                top = height / 6
                right = 1100
                bottom = 290
                # Cropped image of above dimension
                # (It will not change orginal image)
                im1 = image.crop((left, top, right, bottom))

                # Shows the image in image viewer
                cover = resizeimage.resize_width(im1, 120)
                cover.save("{0}/{1}_resized.png".format(output_dir, self.filename), image.format)

    @staticmethod
    def replace_all(text, dic):
        """
        Replace text with given dict criteria
        """
        for i, j in dic.items():
            text = text.replace(i, j)
        return text

    def create_graph(self, output_dir='/tmp'):
        """Create graph html file using plotly offline-mode from dataframe object"""

        fig = subplots.make_subplots(rows=2, cols=1, shared_xaxes=True, print_grid=False)
        for name, value in self.data.items():
            row = 1
            col = 1
            if name == 'ohlc':
                if value.empty:  # empty dataframe:
                    print('Unable to find ohlc data for {0}, passing...'.format(self.pair))
                    return
                value["time"] = pandas.to_datetime(value["closeTime"], unit="ms")
                item = go.Candlestick(x=value.time,
                                      open=value.open,
                                      high=value.high,
                                      low=value.low,
                                      close=value.close,
                                      name=self.pair)


            elif name == 'event':
                # dataframe is mutable so we cannot reference exisiting values by hashing
                # therefore we will substitute buy/sell with and rgb value for red/green
                replace = {"OPEN": "rgb(0,255,0)", "BUY": "rgb(0,255,0)",
                           "CLOSE": "rgb(255,0,0)", "SELL": "rgb(255,0,0)"
                           }
                value = self.replace_all(value, replace)

                item = go.Scatter(x=pandas.to_datetime(value["date"], unit="ms"),
                                  y=value['current_price'],
                                  name="events",
                                  mode='markers',
                                  marker=dict(size=16, color=value['result']))
            elif 'pivot' in name:
                item = go.Scatter(x=pandas.to_datetime(value["date"], unit="ms"),
                                  y=value['value'],
                                  name=name,
                                  mode='markers')

                # add rsi graph in second subply (below) if it exists
            elif 'RSI' in name or 'signal' in name:
                item = go.Scatter(x=pandas.to_datetime(value["date"], unit="ms"),
                                  y=value['value'],
                                  name=name)
                row = 2
                # add tsi graph in second subply (below) if it exists


            elif 'STOCHF' in name:
                item = go.Bar(x=pandas.to_datetime(value["date"], unit="ms"),
                              y=value['value'],
                              name=name)
                row = 2

            elif 'SHOOTINGSTAR' in name or 'SPINNINGTOP' in name:
                item = go.Bar(x=pandas.to_datetime(value["date"], unit="ms"),
                              y=value['value'],
                              name=name)
                row = 2

            elif 'Sup_Res' in name:
                item = go.Scatter(x=pandas.to_datetime(value["date"], unit="ms"),
                                  y=value['value'],
                                  mode='markers',
                                  name="Resistance")

            else:
                item = go.Scatter(x=pandas.to_datetime(value["date"], unit="ms"),
                                  y=value['value'],
                                  name=name)
            fig.append_trace(item, row, col)

            if name == "ohlc" and self.volume:
                increasing_color = '#17BECF'
                decreasing_color = '#7F7F7F'
                colors = []

                for i in range(len(value.close)):
                    if i != 0:
                        if value.close.iloc[i] > value.close.iloc[i-1]:
                            colors.append(increasing_color)
                        else:
                            colors.append(decreasing_color)
                    else:
                        colors.append(decreasing_color)

                item = go.Bar(x=value.time,
                              y=value.volume,
                              name="volume",
                              marker=dict(color=colors))
                row = 2
                fig.append_trace(item, row, col)

        now = datetime.datetime.now()
        date = now.strftime('%Y-%m-%d_%H-%M-%S')
        env = config.main.base_env
        self.filename = "{0}/{1}_{2}_{3}-{4}.html".format(output_dir, self.pair, env,
                                                          date, self.interval)
        py.plot(fig, filename=self.filename, auto_open=False)

    def insert_data(self, dframe):
        """
        insert ohlc data for creating graphs
        """
        self.data = {'ohlc': dframe}

    def get_data(self):
        """Fetch data from redis"""
        redis = Redis(test=self.test)
        list_of_series = []
        index = redis.get_items(self.pair, self.interval)

        main_indicators = config.main.indicators.split()
        ind_list = []
        for i in main_indicators:
            split = i.split(';')
            ind = split[1] + '_' + split[2].split(',')[0]
            ind_list.append(ind)
        list_of_results = defaultdict(list)
        for index_item in index:
            result_list = {}
            for ind in ind_list:
                try:
                    result_list[ind] = ast.literal_eval(redis.get_item(index_item, ind).decode())
                except AttributeError:
                    pass
            try:
                result_list['ohlc'] = ast.literal_eval(redis.get_item(index_item,
                                                                      'ohlc').decode())['result']
            except AttributeError as error:
                LOGGER.error("Error, unable to find ohlc data for %s %s %s"
                             % (index_item, ind, error))
            try:
                result_list['event'] = ast.literal_eval(redis.get_item(index_item,
                                                                       'event').decode())
            except AttributeError:  # no event for this time period, so skip
                pass
            rehydrated = pickle.loads(zlib.decompress(result_list['ohlc']))
            list_of_series.append(rehydrated)
            for ind in ind_list:
                try:
                    list_of_results[ind].append((result_list[ind]['result'],
                                                 result_list[ind]['date']))
                except KeyError:
                    pass
            try:
                list_of_results['event'].append((result_list['event']['result'],
                                                 result_list['event']['current_price'],
                                                 result_list['event']['date']))
            except KeyError:
                pass
        dataframes = {}

        dataframes['ohlc'] = pandas.DataFrame(list_of_series)
        dataframes['event'] = pandas.DataFrame(list_of_results['event'],
                                               columns=['result', 'current_price', 'date'])
        for ind in ind_list:
            dataframes[ind] = pandas.DataFrame(list_of_results[ind], columns=['value', 'date'])
        self.data = dataframes
