import logging
import numbers
import time

def backoff(base : numbers = 0.2, multiplier : numbers = 1.2, cap : numbers = 1, retries : int = 3, logger=logging.getLogger(__name__)):
    def decorator(func):
        def wrapper(*args, **kwargs):
            retry = 0
            delay = base
            while retry <= retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retry += 1
                    if retry > retries:
                        raise e
                    logger.error(f"Failed to execute function '{func.__name__}'. Retrying in {delay} seconds...")
                    time.sleep(delay)
                    delay = max(cap, delay * multiplier)
        return wrapper
    return decorator
