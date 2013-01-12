import re
import os
from resettabletimer import ResettableTimer
from watchdog.events import FileSystemEventHandler

class WDEventHandler(FileSystemEventHandler):
    def __init__(self, gus):
        self.timer = None
        self.gus   = gus
    def timer_callback(self):
        self.gus.render_site()
        self.timer = None
    def do_something(self, event):
        if re.match('.*~$', event.src_path):
            return
        if re.match("^.*%s\..*\.sw.$" % os.path.sep, event.src_path):
            return
        if self.timer is None:
            self.timer = ResettableTimer(0.5, self.timer_callback)
        else:
            self.timer.reset()
        print "mod or create %s" % event.src_path
    def on_created(self, event):
        self.do_something(event)
    def on_modified(self, event):
        self.do_something(event)
