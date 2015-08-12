from selenium_class import SeleniumTest
import os

class TestLinePlot(SeleniumTest):
  def __init__(self):
    os.system('python ./examples/charts/file/lines.py')
    driver = self.get_driver()
    driver.get('http://localhost:8080/lines.html')

    # Assert Canvas Hash
    canvas = driver.find_element_by_tag_name('canvas')
    assert canvas.get_attribute('data-hash') == 'e6b53c5483cddf5b005fbcd459748c37'

    # Assert logo is present
    assert self.driver.find_element_by_css_selector("a.bk-logo.bk-logo-small")

    # Find the 7th bar item and click it
    self.driver.find_element_by_css_selector('.plotdiv > div > div > div > table > tbody > tr:nth-child(1) > td.bk-plot-above.bk-sidebar.bk-toolbar-active > div > ul:nth-child(7) > li:nth-child(1) > button').click()

    # Assert modal has a primary button
    assert self.driver.find_element_by_css_selector(".bk-bs-modal-footer > button.bk-bs-btn.bk-bs-btn-primary")

    driver.quit()

TestLinePlot()
