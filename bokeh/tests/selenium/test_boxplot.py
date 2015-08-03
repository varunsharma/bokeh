from selenium_class import SeleniumTest
import os

class TestBoxPlot(SeleniumTest):
  def __init__(self):
    os.system('python ../../../examples/plotting/file/boxplot.py')
    driver = self.get_driver()
    driver.get('http://localhost:8080/boxplot.html')
    canvas = driver.find_element_by_tag_name('canvas')
    assert canvas.get_attribute('data-hash') == '0490674b7cbcebe8db8b25a7593d47f2'
    driver.quit()

TestBoxPlot()