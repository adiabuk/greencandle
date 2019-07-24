#!/usr/bin/env python

"""Create candlestick graphs from OHLC data"""

import ast
import os
import time
import pickle
import zlib
import pandas
from selenium import webdriver
from pyvirtualdisplay import Display
import plotly.offline as py
import plotly.graph_objs as go


from PIL import Image
from resizeimage import resizeimage
from .redis_conn import Redis

PATH = os.getcwd() + "/graphs/in/"
PATH = '/tmp/'

def get_screenshot(filename=None):
    """Capture screenshot using selenium/firefox in Xvfb """
    display = Display(visible=0, size=(1366, 768))
    display.start()

    profile = webdriver.FirefoxProfile()
    profile.set_preference("browser.download.folderList", 2)  # custom location
    profile.set_preference("browser.download.manager.showWhenStarting", False)
    profile.set_preference("browser.download.dir", "/tmp")
    profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "image/png")

    driver = webdriver.Firefox(firefox_profile=profile)
    driver.get("file://{0}/{1}.html".format(PATH, filename))
    driver.save_screenshot("{0}/{1}.png".format(PATH, filename))
    time.sleep(10)
    driver.quit()
    display.stop()

def resize_screenshot(filename=None):
    """Resize screenshot to thumbnail - for use in API"""
    with open("{0}/{1}.png".format(PATH, filename), "r+b") as png_file:
        with Image.open(png_file) as image:
            cover = resizeimage.resize_width(image, 120)
            cover.save("{0}/{1}_resized.png".format(PATH, filename), image.format)

def create_graph(dataframe, dataframe2, dataframe3, dataframe4, dataframe5, pair):
    """Create graph html file using plotly offline-mode from dataframe object"""
    py.init_notebook_mode()
    dataframe["time"] = pandas.to_datetime(dataframe["closeTime"], unit="ms")
    candles = go.Candlestick(x=dataframe.time + pandas.Timedelta(hours=1),
                             open=dataframe.open,
                             high=dataframe.high,
                             low=dataframe.low,
                             close=dataframe.close)
    ema18 = go.Scatter(x=dataframe2['date'], # assign x as the dataframe column 'x'
                       y=dataframe2['value'],
                       name='EMA-18')
    ema25 = go.Scatter(x=dataframe3['date'], # assign x as the dataframe column 'x'
                       y=dataframe3['value'],
                       name='EMA-25')
    wma7 = go.Scatter(x=dataframe4['date'], # assign x as the dataframe column 'x'
                      y=dataframe4['value'],
                      name='WMA-7')
    events = go.Scatter(x=dataframe5['date'],
                        y=dataframe5['current_price'],
                        name="events",
                        mode='markers+text',
                        text=dataframe5['result'],
                        textposition='top center',
                        marker=dict(size=16, color=dataframe5['result']))

    filename = "simple_candlestick_{0}".format(pair)
    py.plot([candles, ema18, ema25, wma7, events], filename="{0}/{1}.html".format(PATH, filename), auto_open=False)

def get_data(test=False, db=0):
    """Fetch data from redis"""
    print('Using db: {0}'.format(db))
    redis = Redis(test=test, db=db)
    list_of_series = []
    list_of_ema18 = []
    list_of_ema25 = []
    list_of_wma7 = []
    list_of_events = []
    index = redis.get_items('ETHBTC', '1m')
    for index_item in index:
        ema18 = ast.literal_eval(redis.get_item(index_item, 'EMA-18').decode())
        ema25 = ast.literal_eval(redis.get_item(index_item, 'EMA-25').decode())
        wma7 = ast.literal_eval(redis.get_item(index_item, 'WMA-7').decode())
        ohlc = ast.literal_eval(redis.get_item(index_item, 'ohlc').decode())['result']
        try:
            event = ast.literal_eval(redis.get_item(index_item, 'trigger').decode())
            list_of_events.append((event['result'], event['current_price'], event['date']))
        except AttributeError:  # no event for this time period, so skip
            pass
        rehydrated = pickle.loads(zlib.decompress(ohlc))
        list_of_series.append(rehydrated)
        list_of_ema18.append((ema18['result'], ema18['date']))
        list_of_ema25.append((ema25['result'], ema25['date']))
        list_of_wma7.append((wma7['result'], wma7['date']))

    dataframe = pandas.DataFrame(list_of_series)
    dataframe2 = pandas.DataFrame(list_of_ema18, columns=['value', 'date'])
    dataframe3 = pandas.DataFrame(list_of_ema25, columns=['value', 'date'])
    dataframe4 = pandas.DataFrame(list_of_wma7, columns=['value', 'date'])
    dataframe5 = pandas.DataFrame(list_of_events, columns=['result', 'current_price', 'date'])
    return dataframe, dataframe2, dataframe3, dataframe4, dataframe5
