import time
import logging
import sys
from constants import DELAY_INTERVAL, DELAY_DURATION

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler(sys.stdout)])

class RateLimiting:
    """This class simulates Network throttling mechanism. The proxy server will be scheduled to reduce network traffic
        through it. After a specific time the network will be throttled. Request will be delayed at proxy server for
        a certain time. """
    def __init__(self):
        self._last_delay = time.time()
        self._delay_active = False
        self._delay_start = None
        self._current_time = None

    def check_in_delay_period(self):
        """Checking if the network is on delay period. If yes it returns true, otherwise it returns false."""
        self._current_time = time.time()
        if not self._delay_active and (self._current_time - self._last_delay) >= DELAY_INTERVAL:
            logging.info("Entering delay period...")
            self._delay_active = True
            self._delay_start = self._current_time
        elif self._delay_active and (self._current_time - self._delay_start) >= DELAY_DURATION:
            logging.info("Exiting delay period...")
            self._delay_active = False
            self._last_delay = self._current_time

        return self._delay_active

