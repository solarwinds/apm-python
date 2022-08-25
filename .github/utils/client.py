import logging
import os
import sys
import time
import requests


level = logging.DEBUG
logger = logging.getLogger()
logger.setLevel(level)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(level)
formatter = logging.Formatter('%(levelname)s | %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# we need to wait for the Oboe reporter to be ready first, thus add some wait time here
time.sleep(30)

# request to instrumented Flask server
resp = requests.get("http://{}:{}/test/".format(
    os.getenv("FLASK_RUN_HOST"),
    os.getenv("FLASK_RUN_PORT"),
))
logger.debug("Response headers from Flask server:")
logger.debug(resp.headers)

# we give the reporter more time to finish trace export before exit
time.sleep(30)
