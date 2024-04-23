#!/usr/bin/env python
#pylint: disable=invalid-name

"""
Selenium unit test module
"""

import os
import time
import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from pyvirtualdisplay import Display

class TestGc(unittest.TestCase):
    """
    Main test module for GC selenium testing
    """
    def setUp(self):
        """
        Set up display and browser
        """
        self.display = Display(visible=0, size=(1024, 768))
        self.display.start()
        profile = webdriver.FirefoxProfile()
        profile.set_preference("network.security.ports.banned.override", "6666")
        self.driver = webdriver.Firefox(firefox_profile=profile,
                                        executable_path='/usr/local/bin/geckodriver')
        self.driver.implicitly_wait(30)
        self.base_url = "https://www.google.com/"
        self.verificationErrors = []
        self.accept_next_alert = True

    def test_gc(self):
        """
        Selenium test steps
        """
        # Test name: gc
            # Test name: test1
        # Step # | name | target | value
        self.driver.get(os.environ['HOST'])
        # window size
        self.driver.set_window_size(1666, 900)
        # Menu
        self.driver.find_element(By.CSS_SELECTOR, ".hamburger:nth-child(3)").click()

        # trade
        self.driver.find_element(By.CSS_SELECTOR, "li:nth-child(1) > a").click()

        # login
        self.driver.find_element(By.NAME, "username").click()
        self.driver.find_element(By.NAME, "password").send_keys(os.environ['USER_CREDENTIALS_PSW'])
        self.driver.find_element(By.NAME, "username").send_keys(os.environ['USER_CREDENTIALS_USR'])
        self.driver.find_element(By.CSS_SELECTOR, "p:nth-child(3) > input").click()

        time.sleep(3)
        self.driver.find_element(By.LINK_TEXT, "Main Page").click()
        self.driver.find_element(By.CSS_SELECTOR, ".hamburger:nth-child(3)").click()
        time.sleep(1)

        # trade
        self.driver.find_element(By.CSS_SELECTOR, "li:nth-child(1) > a").click()
        self.driver.find_element(By.LINK_TEXT, "Main Page").click()
        self.driver.find_element(By.CSS_SELECTOR, ".hamburger:nth-child(3)").click()
        time.sleep(1)

        # live data spreadsheet
        self.driver.find_element(By.CSS_SELECTOR, "li:nth-child(2) > a").click()
        self.driver.find_element(By.LINK_TEXT, "Main Page").click()
        self.driver.find_element(By.CSS_SELECTOR, ".hamburger:nth-child(3)").click()
        time.sleep(1)

        # Run commands
        self.driver.find_element(By.CSS_SELECTOR, "li:nth-child(3) > a").click()
        self.driver.find_element(By.LINK_TEXT, "Main Page").click()
        time.sleep(1)
        self.driver.find_element(By.CSS_SELECTOR, ".hamburger:nth-child(3)").click()

        time.sleep(1)
        # Tail GC logs
        self.driver.find_element(By.CSS_SELECTOR, "li:nth-child(4) > a").click()
        self.driver.back()

        # Jenkins CI
        self.driver.find_element(By.CSS_SELECTOR, "li:nth-child(5) > a").click()
        self.driver.back()

        # Docker Hub
        self.driver.find_element(By.CSS_SELECTOR, "li:nth-child(6) > a").click()
        self.driver.back()

        # Github
        self.driver.find_element(By.CSS_SELECTOR, "li:nth-child(7) > a").click()
        self.driver.back()

        # Local files
        self.driver.find_element(By.CSS_SELECTOR, "li:nth-child(8) > a").click()
        self.driver.back()

        # Nagios - SKIP

        # GC Versions - SKIP

        # Extra Trade Actions
        self.driver.find_element(By.CSS_SELECTOR, "li:nth-child(11) > a").click()
        #self.driver.back()

        # logout
        self.driver.find_element(By.LINK_TEXT, "logout").click()

    def tearDown(self):
        # 39 | close |  |
        print("Capturing screenshot....")
        self.driver.save_screenshot("failure.png")
        self.driver.close()
        #self.driver.quit()
        self.display.stop()

if __name__ == "__main__":
    unittest.main()
