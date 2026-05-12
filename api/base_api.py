import time
import sys

class BaseApi:
    def __init__(self):
        self.exc_info = None
        self.data = None
        self.nextUpdate = 0

    def reset(self):
        self.__init__()
    
    def update(self):
        try:
            if self.nextUpdate <= time.time():
                self._get_data()
                self.nextUpdate = time.time() + self._get_update_interval()
        except Exception as e:
            self.exc_info = sys.exc_info()
    
    def _get_data(self):
        return NotImplementedError()

    def _get_update_interval(self):
        return NotImplementedError()