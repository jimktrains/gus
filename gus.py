#!/usr/bin/env python

from page import Page, IndexPage
from datetime import datetime
from markdown import markdown
from textile import textile
import copy
import os
import pystache
import re
import shutil
import tempfile
import time
import yaml

class Gus(object):
    def __init__(self):
        self.renderable_pages = []
        self.renderable_index = []
        self.rendered_pages = False
        self.templates = {}
        self.templates['indices'] = {}
        self.pages = {}

    def page_as_dict(self, page):
        return {
            "name":     page.name,
            "title":    page.metadata['title'],
            "date":     page.metadata['date'],
            "tags":     page.metadata['tags'],
            "content":  self.rendered_pages[page.name + "." + page.metadata['file_ext']][1],
            "metadata": page.metadata
        }
    # This needs a better name
    # basically it calculates all the lists of all the pages
    # and tags and everything else we need
    # Later on it'll calculate rf-idf and tag clouds and the such
    def calculate_properties(self):
        self.render_renderables()
        self.properties['current_time'] = time.time();

        for page_type, info in self.page_types.items():
            self.pages[page_type] = []
        for page in self.renderable_pages:
            if page.metadata['private']:
                continue
            self.pages[page.page_type].append(page)

        for page_type, info in self.page_types.items():
            print "Working on %s" % page_type
            # Sort the pages by date and exclude private pages
            self.pages[page_type].sort( key = lambda page : page.metadata['date'], reverse=True)

            # Allow the templates to see all the pages
            self.properties['all_pages'] = [self.page_as_dict(x) for x in self.renderable_pages]
            self.properties[page_type] = [self.page_as_dict(x) for x in self.pages[page_type]]
            self.properties["last_5_%s" % page_type] = [self.page_as_dict(x) for x in self.pages[page_type][:5]]

            if 'indices' in info:
                for index_name, index_info in info['indices'].items():
                    print "Generating index %s for %s" % (index_name, page_type)
                    pages_for_index = {}
                    for page in self.pages[page_type]:
                        keys = [""]
                        for over in index_info['over']:
                            metadata = page.metadata[over]
                            # Tags are the only property that is a list
                            # To make the rest of this method cleaner,
                            # We will convert everything else to a list
                            # and keep tags as is.
                            if (over != "tags"):
                                metadata = [metadata]
                            new_keys = []
                            for dataum in metadata:
                                for key in keys:
                                    key += "/" + dataum
                                    new_keys.append(key)
                                    if not key in pages_for_index:
                                        pages_for_index[key] = []
                                    pages_for_index[key].append(self.page_as_dict(page))
                            keys = new_keys
                    for key in pages_for_index:
                        self.add_index(page_type, index_name, key, pages_for_index[key])

    def get_site_template(self):
        return self.templates['layout']
    def set_site_template(self, template):
        self.templates['layout'] = template
    def get_index_template(self, page_type, index_name):
        return self.templates['indices'][page_type][index_name]
    def set_index_template(self, page_type, index_name, template):
        if not page_type in self.templates['indices']:
            self.templates['indices'][page_type] = {}
        self.templates['indices'][page_type][index_name] = template
    def get_page_template(self, page_type):
        return self.templates[page_type]
    def set_page_template(self, page_type, template):
        self.templates[page_type] = template
    def get_index_path(self, page_type, index_name, name):
        if name[0] == "/":
            name = name[1:]
        return os.path.join(self.page_types[page_type]['indices'][index_name]['web-directory'], name)
    def get_page_path(self, page_type, name):
        return os.path.join(self.page_types[page_type]['web-directory'], name)
    def add_page(self, page_type, name, content, markup_format):
        self.renderable_pages.append(Page(page_type, name, content, markup_format))
    def add_index(self, page_type, index_name, name, pages):
        self.renderable_index.append(IndexPage(page_type, index_name, name, pages))
    def renderables(self):
        class RenderableIterator:
            def __init__(self, gus):
                self.gus = gus
                self.page_i  = 0
                self.index_i = 0
            def __iter__(self):
                return self
            def next(self):
                if self.page_i < len(self.gus.renderable_pages):
                    page = self.gus.renderable_pages[self.page_i]
                    self.page_i += 1
                    return (self.gus.get_page_path(page.page_type, page.name),
                            self.gus.get_page_template(page.page_type),
                            page.markup_renderer,
                            page.content,
                            page.metadata)
                if self.index_i < len(self.gus.renderable_index):
                    page = self.gus.renderable_index[self.index_i]
                    self.index_i += 1
                    return (self.gus.get_index_path(page.page_type, page.index_name, page.name),
                            self.gus.get_index_template(page.page_type, page.index_name),
                            lambda x : x,
                            "",
                            { "pages": page.pages, 'nopagelayout': False,  'nolayout': False, "file_ext": "html"} )
                raise StopIteration()
        return RenderableIterator(self)

    def render_renderables(self):
        self.rendered_pages = {}
        for (path, page_template, markup_renderer, content, metadata) in self.renderables():
            print path
            # Remove all lines begining with % because those
            # are our metadata lines (and I guess could be used
            # as comments in the template because of how I do this)
            page_rendered = re.sub('^\%.*$\s+', '', content, 0, re.MULTILINE)

            props = dict(metadata.items() + self.properties.items())

            # Render the page with mustache
            # Then the page is rendered with the markup (textile or markdown)
            props['body'] = page_rendered
            props['body'] = pystache.render(props['body'], props)
            props['body'] = markup_renderer(props['body'])
            props['on_page'] = False

            # The page rendered into the page-template is what's used
            # is the value used in further mustache templates
            rendered_wo_layout = pystache.render(page_template, props)

            props['on_page'] = True
            # Now we render the page into its page-template
            if not metadata['nopagelayout']:
                props['body'] = pystache.render(page_template, props)
                # The page rendered into the page-templates is then
                # rendered into the site layout.
                if not metadata['nolayout']:
                    props['body'] = pystache.render(self.templates['layout'], props)
            self.rendered_pages[path + '.' + props['file_ext']] = (props['body'], rendered_wo_layout)
        return self.rendered_pages
