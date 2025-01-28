#!/usr/bin/env python
#pylint: disable=invalid-name

"""
Selenium unit test module
"""
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from pyvirtualdisplay import Display
from greencandle.lib.common import arg_decorator

@arg_decorator
def main():
    """
    Set up display and browser
    """
    display = Display(visible=0, size=(1024, 768))
    display.start()
    profile = webdriver.FirefoxProfile()
    profile.set_preference("network.security.ports.banned.override", "6666")
    driver = webdriver.Firefox(firefox_profile=profile,
                                    executable_path='/usr/local/bin/geckodriver')
    driver.implicitly_wait(30)
    base_url = "https://cryptobubbles.net/"
    dt_stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    path = '/data/bub_sentiment/'
    driver.get(base_url)
    driver.set_window_size(1666, 900)

    # select binance
    driver.find_element(By.CSS_SELECTOR, ".select-button").click()
    driver.find_element(By.CSS_SELECTOR, "fieldset:nth-child(3) > .solid-button:nth-child(2)"
                        ).click()

    time.sleep(3)
    # hour
    driver.find_element(By.CSS_SELECTOR, ".tab:nth-child(1)").click()
    time.sleep(3)
    driver.save_screenshot(f"{path}hour_{dt_stamp}.png")

    # day
    driver.find_element(By.CSS_SELECTOR, ".tab:nth-child(2)").click()
    time.sleep(3)
    driver.save_screenshot(f"{path}day_{dt_stamp}.png")

    driver.close()
    #driver.quit()
    display.stop()

if __name__ == "__main__":
    main()
