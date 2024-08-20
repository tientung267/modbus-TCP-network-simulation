import time
import logging
import sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[logging.StreamHandler(sys.stdout)])

DELAY_INTERVAL = 30  # Time in seconds after which delay should be introduced
DELAY_DURATION = 10  # Time in seconds indicates how long the throttling of the network should take place

class RateLimiting:
    """This class simulates Network throttling mechanism. The gateway server will be scheduled to reduce network traffic
        through it. After a specific time the network will be throttled. Request will be delayed at gateway Server for
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

