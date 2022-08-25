import os
import time
import requests


# we need to wait for the Oboe reporter to be ready first, thus add some wait time here
time.sleep(10)

# request to instrumented Flask server
requests.get("http://{}:{}/test/".format(
    os.getenv("FLASK_RUN_HOST"),
    os.getenv("FLASK_RUN_PORT"),
))
