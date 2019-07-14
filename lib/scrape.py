#!/usr/bin/env python
# -*- coding: utf-8 -*-
#pylint: disable=broad-except

"""
Selenium Webscraper for tradingview signals
"""

import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.firefox.options import Options

def scrape_data(binary="firefox"):
    """
    Scrape data from site using selenium
    """
    if binary == "chrome":
        path_to_chromedriver = "/usr/bin/chromedriver"
        options = webdriver.ChromeOptions()
        options.add_argument("headless")
        options.add_argument("window-size=1200,1100")
        driver = webdriver.Chrome(executable_path=path_to_chromedriver, chrome_options=options)
    else:
        options = Options()
        options.add_argument("--headless")
        driver = webdriver.Firefox(firefox_options=options)

    driver.get("https://www.tradingview.com/cryptocurrency-signals/")
    results = {}
    wait = WebDriverWait(driver, 10)
    time.sleep(15)
    driver.implicitly_wait(30)
    driver.find_element_by_css_selector("div.tv-screener-toolbar.tv-screener-toolbar--standalone"
                                        ".tv-screener-toolbar--standalone_sticky > div.tv-"
                                        "screener-toolbar__button.tv-screener-toolbar__button--"
                                        "options.tv-screener-toolbar__button--square.apply-common-"
                                        "tooltip.common-tooltip-fixed > svg.tv-screener-toolbar__"
                                        "button-icon").click()
    driver.find_element_by_xpath("/html/body/div[13]/div/div[2]/input").click()
    driver.find_element_by_xpath("/html/body/div[13]/div/div[2]/input").send_keys("EXC")

    driver.find_element_by_xpath("/html/body/div[13]/div/div[3]/div[1]/div/div/div[4]/"
                                 "div[2]/div/span").click()
    driver.find_element_by_xpath("/html/body/div[13]/div/div[4]/div[3]/div[1]/div[2]/label/label/"
                                 "span[2]").click()
    driver.find_element_by_xpath("/html/body/div[13]/div/div[1]/div[4]").click()

    #Select 5m as interval
    driver.find_element_by_xpath('//*[@id="js-screener-container"]/div[2]/div[7]/div[2]').click()
    driver.find_element_by_xpath(' //*[@id="js-screener-container"]/div[2]/div[7]/div[3]/div/div[1]/div[1]/div').click()
    for i in range(1, 500):
        try:
            item = driver.find_element_by_xpath("//div[@id='js-screener-container']/div[4]/"
                                                "table/tbody/tr[{0}]".format(i))
            actions = ActionChains(driver)
            driver.execute_script("return arguments[0].scrollIntoView();", item)
            actions.move_to_element(item).perform()
            line = item.text
        except NoSuchElementException:
            #print("no element")
            break
        except Exception as ex:
            #print("exception", ex)
            wait.until(EC.staleness_of(item))
            #line = u"".join(line).encode("utf-8").strip()
            continue

        try:
            li = line.replace("Strong ", "Strong_").split()
            if "BTC" in li[0]:
                #print(line)
                results[li[0]] = li[-2]

        except Exception as e:
            #print("exception2", e)
            continue
    #driver.close()
    driver.quit()
    return results

if __name__ == "__main__":
    data = scrape_data("firefox")
    for key, value in data.items():
        print(key, value)
