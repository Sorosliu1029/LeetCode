import time
from functools import wraps

class Timer:
    def __init__(self, func=time.process_time):
        self.elapsed = 0.0
        self._func = func
        self._start = None
    
    def start(self):
        if self._start is not None:
            raise RuntimeError('Already started')
        self._start = self._func()
    
    def stop(self):
        if self._start is None:
            raise RuntimeError('Not started')
        end = self._func()
        self.elapsed += end - self._start
        self._start = None
    
    def reset(self):
        self.elapsed = 0.0

    @property
    def running(self):
        return self._start is not None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()

def timethis(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.process_time()
        r = func(*args, **kwargs)
        end = time.process_time()
        print('Run for {:.3f} seconds'.format(end - start))
        return r
    return wrapper