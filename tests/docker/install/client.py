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


def request_server(attempts=10):
    # Brute force until server responds
    try:
        resp = requests.get("http://{}:{}/test/".format(
            os.getenv("FLASK_RUN_HOST"),
            os.getenv("FLASK_RUN_PORT"),
        ))
        logger.debug("Response headers from Flask server:")
        logger.debug(resp.headers)
    except:
        logger.debug("Server not responding. Will try up to {} more times".format(attempts))
        attempts -= 1
        if attempts > 0:
            time.sleep(1)
            request_server(attempts)


if __name__ == "__main__":
    request_server()
    logger.debug("Waiting a moment in case reporter needs extra time...")
    time.sleep(10)
    logger.debug("Server requests complete.\n")
