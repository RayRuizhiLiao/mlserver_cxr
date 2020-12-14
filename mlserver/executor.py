import gin
import threading
import time

from absl import logging


@gin.configurable
class DelayedExecutor(threading.Thread):
    def __init__(self, delay, interval=1.0):
        super(DelayedExecutor, self).__init__()

        self.delay = delay
        self.interval = interval

        self._lock = threading.Lock()
        self._fns = {}

    def delayed_run(self, key, fn):
        with self._lock:
            self._fns[key] = (time.time(), fn)

    def _run(self):
        with self._lock:
            keys = []
            for (key, (t, fn)) in self._fns.items():
                until_now = time.time() - t
                logging.info(f'{key} has not been observed in {until_now:.1f} seconds.')

                if until_now > self.delay:
                    thread = threading.Thread(target=fn)
                    thread.start()

                    keys.append(key)

            for key in keys:
                del self._fns[key]

    def run(self):
        while True:
            self._run()
            time.sleep(self.interval)