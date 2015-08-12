from selenium_class import SeleniumTest
import os

class TestBoxPlot(SeleniumTest):
  def __init__(self):
    os.system('python ../../../examples/plotting/file/lines.py')
    driver = self.get_driver()
    driver.get('http://localhost:8080/line.html')

    canvas = driver.find_element_by_tag_name('canvas')
    assert canvas.get_attribute('data-hash') == '26cc3a0be7edf3babe6e32d34851fb55'



    driver.quit()

TestBoxPlot()