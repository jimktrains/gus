import sys
import time
import threading

class ResettableTimer(threading.Thread):
    def __init__(self, maxtime, callback):
        self.maxtime  = maxtime
        self.counter  = 0
        self.inc      = maxtime / 10.0
        self.callback = callback
        threading.Thread.__init__(self)
        self.setDaemon(True)
        self.start();
    def reset(self):
        self.counter = 0
    def run(self):
        self.counter = 0
        while self.counter < self.maxtime:
            self.counter += self.inc
            time.sleep(self.inc)
        self.callback()
