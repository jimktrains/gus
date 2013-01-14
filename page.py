#!/usr/bin/env python

from datetime import datetime
from markdown import markdown
from textile import textile
import os
import re
import time

class Page:
    def __init__(self, page_type, name, content, markup_format):
        self.page_type = page_type
        self.name      = name
        self.content   = content
        self.markup_format = markup_format
        if self.markup_format == ".textile":
            self.markup_renderer = textile
        elif self.markup_format == ".md":
            self.markup_renderer = markdown
        else:
            self.markup_renderer = lambda x : x
        self.metadata = False
        self.extract_metadata()
    def extract_metadata(self):
        if not self.metadata:
            meta = re.finditer( '^%(\S*) (.*)$', self.content, re.MULTILINE)
            props = {}
            for match in meta:
                name = match.group(1)
                val  = match.group(2)
                # Tags are the exception to properties just
                # being a string.
                if name == 'tags':
                    val = val.split(' ')
                props[name] = val
            self.metadata = props
            self.check_metadata()
        return self.metadata
    def check_metadata(self):
        if self.metadata or self.metadata == {}:
            if not 'title' in self.metadata:
                self.metadata['title'] = None
            if not 'date' in self.metadata:
                self.metadata['date']       = None
                self.metadata['date-year']  = None
                self.metadata['date-month'] = None
                self.metadata['date-day']   = None
            else:
                # I'm not a fan of this
                self.metadata['date']       = datetime.strptime(self.metadata['date'], "%Y-%m-%d")
                self.metadata['date-year']  = str(self.metadata['date'].timetuple()[0])
                self.metadata['date-month'] = "%02d" % self.metadata['date'].timetuple()[1]
                self.metadata['date-day']   = "%02d" % self.metadata['date'].timetuple()[2]
                self.metadata['date']       = self.metadata['date'].strftime("%Y-%m-%d")
            if not 'private' in self.metadata:
                self.metadata['private'] = False
            if not 'tags' in self.metadata:
                self.metadata['tags'] = []
            if not 'nolayout' in self.metadata:
                self.metadata['nolayout'] = False
            if not 'nopagelayout' in self.metadata:
                self.metadata['nopagelayout'] = False
            if not 'file_ext' in self.metadata:
                self.metadata['file_ext'] = 'html'
            self.metadata['name'] = self.name

class IndexPage:
    def __init__(self, page_type, index_name, name, pages):
        self.page_type  = page_type
        self.index_name = index_name
        self.name       = name
        self.pages      = pages
