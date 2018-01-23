# Location of SUT's source code.
SUT_SRC_PATH = '$SUT_SRC_PATH'
# Host where SUT will be running on. Do not change.
SUT_HOST = '127.0.0.1'
# Port that SUT is configured to forward requests to.
# Is used by Interceptor thread.
# !!!Before changing it here, change it in SUT configuration!!!
SUT_FORWARD_PORT = 5000
# Port that SUT is configured to listen to requests on.
# Is used to determine when SUT started and is ready to be tested.
# !!!Before changing it here, change it in SUT configuration!!!
SUT_PORT = 8081
# API method that SUT exposes.
SUT_API_PATH = '/api/image'
# SUT url.
SUT_URL = 'http://{0}:{1}'.format(SUT_HOST, SUT_PORT)