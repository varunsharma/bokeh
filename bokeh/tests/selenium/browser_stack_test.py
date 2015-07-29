from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import NoAlertPresentException
import unittest, time, re
import os
import sys

class Test(unittest.TestCase):
    def setUp(self):
        desired_cap = {'browser': 'Chrome', 'browser_version': '43.0', 'os': 'OS X', 'os_version': 'Yosemite', 'resolution': '1024x768'}
        desired_cap['browserstack.local'] = True
        desired_cap['browserstack.debug'] = True
        try:
           bs_username = os.environ['BROWSERSTACK_USERNAME']
           bs_api_key = os.environ['BROWSERSTACK_API_KEY']
        except KeyError:
           print "Please set BROWSERSTACK_USERNAME and BROWSERSTACK_API_KEY credientials"
           sys.exit(1)
        self.driver = webdriver.Remote(
            command_executor='http://' + bs_username + ':' + bs_api_key + '@hub.browserstack.com:80/wd/hub',
            desired_capabilities=desired_cap)
        self.driver.implicitly_wait(30)
        self.driver.get("http://localhost:8000/periodic.html")
        self.verificationErrors = []
        self.accept_next_alert = True

    def test_(self):
        driver = self.driver
        self.assertTrue(self.is_element_present(By.CSS_SELECTOR, "a.bk-logo.bk-logo-small"))
        driver.find_element_by_xpath("(//button[@type='button'])[2]").click()
        self.assertTrue(self.is_element_present(By.CSS_SELECTOR, "button.bk-bs-btn.bk-bs-btn-primary"))

    def is_element_present(self, how, what):
        try:
            self.driver.find_element(by=how, value=what)
        except NoSuchElementException, e:
            return False
        return True

    def tearDown(self):
        self.driver.quit()
        self.assertEqual([], self.verificationErrors)

if __name__ == "__main__":
    unittest.main()
