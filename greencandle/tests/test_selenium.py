#!/usr/bin/env python

import os
import time
import json
import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from pyvirtualdisplay import Display

class TestGc(unittest.TestCase):
  def setUp(self):
    self.display = Display(visible=0, size=(1024,768))
    self.display.start()
    profile = webdriver.FirefoxProfile()
    self.driver = webdriver.Firefox(firefox_profile=profile, executable_path='/usr/local/bin/geckodriver')
    self.driver.implicitly_wait(30)
    self.base_url = "https://www.google.com/"
    self.verificationErrors = []
    self.accept_next_alert = True
  def teardown(self):
    self.driver.quit()

  def test_gc(self):
    # Test name: gc
        # Test name: test1
    # Step # | name | target | value
    # 1 | open | / |
    self.driver.get(os.environ['HOST'])
    # 2 | setWindowSize | 1666x600 |
    self.driver.set_window_size(1666, 600)
    # 3 | click | css=.hamburger:nth-child(3) |
    self.driver.find_element(By.CSS_SELECTOR, ".hamburger:nth-child(3)").click()
    # 4 | click | css=li:nth-child(1) > a |
    self.driver.find_element(By.CSS_SELECTOR, "li:nth-child(1) > a").click()
    # 5 | click | name=username |
    self.driver.find_element(By.NAME, "username").click()
    # 6 | type | name=password d|
    self.driver.find_element(By.NAME, "password").send_keys(os.environ['USER_CREDENTIALS_PSW'])
    # 7 | type | name=username |
    self.driver.find_element(By.NAME, "username").send_keys(os.environ['USER_CREDENTIALS_USR'])
    # 8 | click | css=p:nth-child(3) > input |
    self.driver.find_element(By.CSS_SELECTOR, "p:nth-child(3) > input").click()

    #self.driver.save_screenshot("failure.png")
    time.sleep(5)
    # 9 | click | linkText=Main Page |
    self.driver.find_element(By.LINK_TEXT, "Main Page").click()
    # 10 | click | css=.hamburger:nth-child(3) |

    self.driver.find_element(By.CSS_SELECTOR, ".hamburger:nth-child(3)").click()
    # 11 | click | css=li:nth-child(2) > a |
    self.driver.find_element(By.CSS_SELECTOR, "li:nth-child(2) > a").click()
    # 12 | click | linkText=Main Page |
    self.driver.find_element(By.LINK_TEXT, "Main Page").click()
    # 13 | click | css=.hamburger:nth-child(3) |
    self.driver.find_element(By.CSS_SELECTOR, ".hamburger:nth-child(3)").click()
    # 14 | click | css=li:nth-child(3) > a |
    self.driver.find_element(By.CSS_SELECTOR, "li:nth-child(3) > a").click()
    # 15 | click | css=form:nth-child(8) > button |
    self.driver.find_element(By.CSS_SELECTOR, "form:nth-child(8) > button").click()
    # 16 | click | linkText=Main Page |
    self.driver.find_element(By.LINK_TEXT, "Main Page").click()
    # 17 | click | css=.hamburger:nth-child(3) |
    self.driver.find_element(By.CSS_SELECTOR, ".hamburger:nth-child(3)").click()
    # 18 | click | css=li:nth-child(4) > a |
    self.driver.find_element(By.CSS_SELECTOR, "li:nth-child(4) > a").click()
    # 19 | click | linkText=Main Page |
    self.driver.find_element(By.LINK_TEXT, "Main Page").click()
    # 20 | mouseOver | linkText=Main Page |
    time.sleep(3)
    #element = self.driver.find_element(By.LINK_TEXT, "Main Page")
    #actions = ActionChains(self.driver)
    #actions.move_to_element(element).perform()
    # 21 | doubleClick | css=#output > li:nth-child(1) |
    #element = self.driver.find_element(By.CSS_SELECTOR, "#output > li:nth-child(1)")
    #actions = ActionChains(self.driver)
    #actions.double_click(element).perform()
    # 22 | doubleClick | css=#output > li:nth-child(1) |
    #element = self.driver.find_element(By.CSS_SELECTOR, "#output > li:nth-child(1)")
    #actions = ActionChains(self.driver)
    #actions.double_click(element).perform()
    # 23 | click | css=.hamburger:nth-child(3) |
    self.driver.find_element(By.CSS_SELECTOR, ".hamburger:nth-child(3)").click()
    # 24 | click | css=li:nth-child(5) > a |
    self.driver.find_element(By.CSS_SELECTOR, "li:nth-child(5) > a").click()
    # 25 | click | css=li:nth-child(6) > a |
    self.driver.back()
    self.driver.find_element(By.CSS_SELECTOR, "li:nth-child(6) > a").click()
    self.driver.back()
    # 26 | click | css=li:nth-child(7) > a |
    self.driver.find_element(By.CSS_SELECTOR, "li:nth-child(7) > a").click()
    self.driver.back()
    # 27 | click | css=li:nth-child(9) > a |
    self.driver.find_element(By.CSS_SELECTOR, "li:nth-child(9) > a").click()
    # 28 | click | css=li:nth-child(10) > a |
    self.driver.find_element(By.LINK_TEXT, "Main Page").click()
    self.driver.find_element(By.CSS_SELECTOR, ".hamburger:nth-child(3)").click()
    self.driver.find_element(By.CSS_SELECTOR, "li:nth-child(10) > a").click()
    # 29 | click | linkText=graphs |
    self.driver.find_element(By.LINK_TEXT, "graphs").click()
    # 30 | click | linkText=Main Page |
    self.driver.find_element(By.LINK_TEXT, "Main Page").click()
    # 31 | click | css=.hamburger:nth-child(3) |
    self.driver.find_element(By.CSS_SELECTOR, ".hamburger:nth-child(3)").click()
    # 32 | click | css=li:nth-child(13) > a |
    self.driver.find_element(By.CSS_SELECTOR, "li:nth-child(13) > a").click()
    # 33 | click | linkText=Main Page |
    self.driver.find_element(By.LINK_TEXT, "Main Page").click()
    # 34 | click | css=.hamburger:nth-child(3) |
    self.driver.find_element(By.CSS_SELECTOR, ".hamburger:nth-child(3)").click()
    # 35 | click | css=.hamburger:nth-child(3) |
    self.driver.find_element(By.CSS_SELECTOR, ".hamburger:nth-child(3)").click()
    # 36 | click | css=.hamburger:nth-child(3) |
    self.driver.find_element(By.CSS_SELECTOR, ".hamburger:nth-child(3)").click()
    # 37 | click | css=li:nth-child(1) > a |
    self.driver.find_element(By.CSS_SELECTOR, "li:nth-child(1) > a").click()
    # 38 | click | linkText=logout |
    self.driver.find_element(By.LINK_TEXT, "logout").click()


  def tearDown(self):
    # 39 | close |  |
    self.driver.save_screenshot("failure.png")
    self.driver.close()
    #self.driver.quit()
    self.display.stop()

if __name__ == "__main__":
    unittest.main()
