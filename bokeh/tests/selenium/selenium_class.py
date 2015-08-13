from selenium import webdriver
import os

class SeleniumTest():
  try:
    bs_username = os.environ['BROWSERSTACK_USERNAME']
    bs_api_key = os.environ['BROWSERSTACK_API_KEY']
  except KeyError:
    print "Please set BROWSERSTACK_USERNAME and BROWSERSTACK_API_KEY credientials"
    sys.exit(1)
  url = 'http://{bs_username}:{bs_api_key}@hub.browserstack.com:80/wd/hub'.format(bs_username=bs_username, bs_api_key=bs_api_key)
  desired_capabilities = {
    'browser': 'Chrome',
    'browser_version': '43.0',
    'os': 'OS X',
    'os_version': 'Yosemite',
    'resolution': '1024x768',
    'browserstack.local': True,
    'browserstack.debug': True
  }
  driver = webdriver.Remote(command_executor=url, desired_capabilities=desired_capabilities)

  @classmethod
  def get_driver(cls):
    return cls.driver
