import socket
import subprocess
import threading
from urllib.request import urlopen
from urllib.request import Request

import test_config as conf
import time

from flask import Flask
from flask import request


class PostRequestsInterceptor(object):
    """Simple Flask server that intercepts POST requests to /api/image url on
    5000 port. It extracts each request data and stores it into a shared
    collection which tests have access to and can poll at any moment. Should be
    started before tests.
    """

    def __init__(self,
                 path=conf.SUT_API_PATH,
                 port=conf.SUT_FORWARD_PORT,
                 method='POST'):
        """
        :param path: path to intercept HTTP requests to
        :param port: port to intercept HTTP requests to
        :param method: type of HTTP requests (GET, POST, etc.) to intercept
        """

        self.intercepted_data = []
        self.port = port
        self.app = Flask(__name__)
        self.app.add_url_rule(path,
                              endpoint=None,
                              view_func=self.api_image_POST,
                              methods=[method])

    def start(self):
        """Starts interceptor thread and returns instance of self.
        """

        self.thread = threading.Thread(target=self.app.run,
                                       kwargs={'port': self.port})
        self.thread.daemon = True

        try:
            self.thread.start()
            time.sleep(1) # Naive wait to let flask initialize
            return self
        except KeyboardInterrupt:
            self.app._stop()
            exit(1)

    def api_image_POST(self):
        """Handler for POST requests to /api/image.
        Stores request data to a shared collection and replies 200 OK response.
        """

        self.intercepted_data.append(request.data)
        # Return 200 OK to let Demo Zuul proxy know that message was forwarded.
        return "", 200, {}

    def get_last_intercepted_data(self, timeout_secs=5):
        """Returns last intercepted request data as a String.

        :param timeout_secs: seconds to wait for data if it has not
                             been intercepted yet
        :return: byte array with intercepted data
        :raise: TimeoutError if data was not intercepted in within
                             given timeout (5 seconds by default)
        """

        start_time = time.time()
        while not self.intercepted_data:
            if time.time() - start_time > timeout_secs:
                raise TimeoutError('No requests were intercepted in'
                                   ' {0} seconds'.format(timeout_secs))
            # Poll intercepted_data every second
            time.sleep(1)

        return self.intercepted_data.pop()


class DemoZuulProxyRunner(object):
    """Wrapper class to start and stop Demo Zuul Proxy service.
    """

    def __init__(self,
                 src_path=conf.SUT_SRC_PATH,
                 port=conf.SUT_PORT,
                 timeout_secs=30):
        """
        :param src_path: absolute path to a folder where Demo Zuul Proxy source
                         code is located
        :param port: port to monitor to determine that Demo Zuul Proxy is up
                     and running
        :param timeout_secs: seconds to wait for Demo Zuul Proxy to start and
                             initialize
        """

        self.src_path = src_path
        self.port = port
        self.timeout_secs = timeout_secs
        self.p = None # Object to hold Demo Zuul Proxy sub-process

    def start(self):
        """Starts Demo Zuul Proxy and returns instance of this wrapper.
        :return: instance of this wrapper
        """

        self.p = subprocess.Popen('./mvnw spring-boot:run',
                                  cwd=self.src_path,
                                  shell=True,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)

        start_time = time.time()
        # Probe Demo Zuul Proxy's host:port to determine if it started
        while True:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if sock.connect_ex((conf.SUT_HOST, self.port)) == 0:
                # If there's no error code still give Demo Zuul Proxy another
                # second to finish initialization and be ready to process
                # requests. I did not find a better way than simple sleep.
                time.sleep(1)
                break

            if time.time() - start_time > self.timeout_secs:
                raise TimeoutError('SUT did not start in'
                                   ' {0} seconds'.format(self.timeout_secs))
            # Try every couple seconds until success or timeout
            time.sleep(2)

        return self

    def stop(self):
        """Stops running Demo Zuul Proxy service.
        """
        self.p and self.p.terminate()


def post(json):
    """Calls /api/image method of Demo Zuul Proxy via POST request.

    :param json: String with JSON to feed to /api/image.
    """
    headers = {
        'Content-Type': 'application/json'
    }
    request = Request(conf.SUT_URL + conf.SUT_API_PATH,
                      json.encode(),
                      method='POST',
                      headers=headers)
    urlopen(request).read()
