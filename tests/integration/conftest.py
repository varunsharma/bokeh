from __future__ import absolute_import, print_function
import os
import pytest

from bokeh.io import output_file
from .webserver import SimpleWebServer


@pytest.fixture(scope='session', autouse=True)
def server(request):
    server = SimpleWebServer()
    server.start()

    def stop_server():
        server.stop()
    request.addfinalizer(stop_server)

    return server


@pytest.fixture(scope='session')
def base_url(request, server):
    return 'http://%s:%s' % (server.host, server.port)


@pytest.fixture
def output_file_url(request, base_url):

    filename = request.function.__name__ + '.html'
    file_path = request.fspath.dirpath().join(filename).strpath

    output_file(file_path, mode='inline')

    def fin():
        os.remove(file_path)
    request.addfinalizer(fin)

    return '%s/%s' % (base_url, file_path)


class ScreenshotTest(object):
    """
    Used for screenshot testings. Use in conjunction with screenshot_test fixture.
    """
    def __init__(self, request):
        # Check for screenshots directory, and if not available make it
        screenshot_dir = request.fspath.dirpath().join('screenshots')
        screenshot_dir.ensure_dir()

        # Check for base screenshot, and if not available:
        # - mark for base_screenshot
        test_file = request.fspath.basename.split('.py')[0]
        test_name = request.function.__name__

        self.base_screenshot_path = screenshot_dir.join(test_file + '__' + test_name + '__base.png')
        if not self.base_screenshot_path.isfile():
            request.keywords['base_screenshot_path'] = self.base_screenshot_path
            request.keywords['need_base_screenshot'] = True

    @property
    def expected_screenshot(self):
        if not self.base_screenshot_path.isfile():
            return 'No screenshot present, one will be taken at end of this test run, please re-run this test'
        else:
            with open(self.base_screenshot_path.strpath, 'rb') as f:
                screenshot = f.read()
            return screenshot


@pytest.fixture
def screenshot_test(request):
    return ScreenshotTest(request)


# This function name allows us to hook into pytests runtime functionality
def pytest_runtest_makereport(__multicall__, item, call):

    report = __multicall__.execute()

    if 'screenshot_test' not in item.fixturenames:
        return report

    if call.when == 'call':
        driver = getattr(item, '_driver', None)
        if driver is not None:
            base_screenshot_path = item.keywords.get('base_screenshot_path')
            if item.keywords.get('need_base_screenshot') and base_screenshot_path:
                driver.get_screenshot_as_file(base_screenshot_path.strpath)
                return report

    return report
