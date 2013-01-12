#!/usr/bin/env python

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

class Renderable:
    # Name should not contain an extention
    def __init__(self, name, page_template, layout_template, markup_format, content, properties, page_type, metadata = False):
        self.name = name
        self.page_template = page_template
        self.markup_format = markup_format
        self.content = content
        self.properties = properties
        self.rendered = False
        self.rendered_wo_layout = False
        self.page_type = page_type
        self.metadata = metadata
        self.check_metadata()
        self.layout_template = layout_template
        self.extract_metadata()
        self.render()
    def as_dict(self):
        return {
            "name":     self.name,
            "title":    self.metadata['title'],
            "date":     self.metadata['date'],
            "tags":     self.metadata['tags'],
            "content":  self.rendered_wo_layout,
            "metadata": self.metadata
        }
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
                self.metadata['date']       = datetime.strptime(self.metadata['date'], self.properties['date-format'])
                self.metadata['date-year']  = str(self.metadata['date'].timetuple()[0])
                self.metadata['date-month'] = "%02d" % self.metadata['date'].timetuple()[1]
                self.metadata['date-day']   = "%02d" % self.metadata['date'].timetuple()[2]
                self.metadata['date']       = self.metadata['date'].strftime(self.properties['date-format'])
            if not 'private' in self.metadata:
                self.metadata['private'] = False
            if not 'tags' in self.metadata:
                self.metadata['tags'] = []
            if not 'nolayout' in self.metadata:
                self.metadata['nolayout'] = False
            self.metadata['name'] = self.name
    def render(self):
        # Remove all lines begining with % because those
        # are our metadata lines (and I guess could be used
        # as comments in the template because of how I do this)
        page_rendered = ""
        if self.content is not None:
            page_rendered = re.sub('^\%.*$', '', self.content, 0, re.MULTILINE)

        props = dict(self.metadata.items() + self.properties.items())

        # Render the page with mustache
        # Then the page is rendered with the markup (textile or markdown)
        props['body'] = page_rendered
        props['body'] = pystache.render(props['body'], props)
        if self.markup_format == ".textile":
            props['body'] = textile(props['body'])
        elif self.markup_format == ".md":
            props['body'] = markdown(props['body'])
        # Now we render the page into its page-template
        props['body'] = pystache.render(self.page_template, props)
        # The page rendered into the page-template is what's used
        # is the value used in further mustache templates
        self.rendered_wo_layout = props['body']
        # The page rendered into the page-templates is then
        # rendered into the site layout.
        if not self.metadata['nolayout']:
            props['body'] = pystache.render(self.layout_template, props)
        self.rendered = props['body']
        return self.rendered

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
                self.metadata['date']       = datetime.strptime(self.metadata['date'], self.properties['date-format'])
                self.metadata['date-year']  = str(self.metadata['date'].timetuple()[0])
                self.metadata['date-month'] = "%02d" % self.metadata['date'].timetuple()[1]
                self.metadata['date-day']   = "%02d" % self.metadata['date'].timetuple()[2]
                self.metadata['date']       = self.metadata['date'].strftime(self.properties['date-format'])
            if not 'private' in self.metadata:
                self.metadata['private'] = False
            if not 'tags' in self.metadata:
                self.metadata['tags'] = []
            if not 'nolayout' in self.metadata:
                self.metadata['nolayout'] = False
            self.metadata['name'] = self.name
class IndexPage:
    def __init__(self, page_type, index_name, name, pages):
        self.page_type  = page_type
        self.index_name = index_name
        self.name       = name
        self.pages      = pages

class Gus(object):
    def __init__(self):
        self.renderable_pages = []
        self.renderable_index = []
        self.pages = {}

    # This needs a better name
    # basically it calculates all the lists of all the pages
    # and tags and everything else we need
    # Later on it'll calculate rf-idf and tag clouds and the such
    def calculate_properties(self):
        self.properties['current_time'] = time.time();

        for page_type, info in self.page_types.items():
            self.pages[page_type] = []
        for page in self.renderable:
            if page.metadata['private']:
                continue
            self.pages[page.page_type].append(page)

        for page_type, info in self.page_types.items():
            # Sort the pages by date and exclude private pages
            self.pages[page_type].sort( key = lambda page : page.metadata['date'], reverse=True)

            # Allow the templates to see all the pages
            self.properties[page_type] = [x.as_dict() for x in self.pages[page_type]]
            self.properties["last_5_%s" % page_type] = [x.as_dict() for x in self.pages[page_type][:5]]

            if 'indices' in info:
                for index_name, index_info in info['indices'].items():
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
                                    pages_for_index[key].append(page.as_dict())
                            keys = new_keys
                    for key in pages_for_index:
                        self.add_index(page_type, index_name, key, pages_for_index[key])

    def get_site_template(self):
        return self.templates['layout']
    def get_index_template(self, page_type, index_name):
        return self.templates['indices'][page_type][index_name]
    def get_page_template(self, page_type):
        return self.templates[page_type],
    def get_index_path(self, page_type, index_name, name):
        if name[0] == "/":
            name = name[1:]
        return os.path.join(self.page_types[page_type]['indices'][index_name]['web-directory'], name)
    def get_page_path(self, page_type, name):
        return os.path.join(self.page_types[page_type]['web-directory'], name)
    def add_page(self, page_type, name, content, markup_format);
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
            def next():
                if self.page_i < len(gus.renderable_pages):
                    page = gus.renderable_pages[self.page_i]
                    self.page_i += 1
                    return (self.get_page_path(page.page_type, page.name),
                            self.get_page_template(page.page_type),
                            page.markup_renderer,
                            page.content,
                            page.metadata)
                if self.index_i < len(gus.renderable_index):
                    page = gus.renderable_pages[self.page_i]
                    self.index_i += 1
                    return (self.get_index_path(page.page_type, page.name, page.index_name),
                            self.get_index_template(page.page_type, page.index_name),
                            lambda x : x,
                            "",
                            { "pages": page.pages } )
        return RenderableIterator(self)

    def render_renderables(self):
        self.rendered_pages = {}
        for (path, page_template, markup_renderer, content, metadata) in self.renderables():
            # Remove all lines begining with % because those
            # are our metadata lines (and I guess could be used
            # as comments in the template because of how I do this)
            page_rendered = re.sub('^\%.*$', '', content, 0, re.MULTILINE)

            props = dict(metadata.items() + self.properties.items())

            # Render the page with mustache
            # Then the page is rendered with the markup (textile or markdown)
            props['body'] = page_rendered
            props['body'] = pystache.render(props['body'], props)
            props['body'] = markup_renderer(props['body'])

            # Now we render the page into its page-template
            props['body'] = pystache.render(page_template, props)
            # The page rendered into the page-template is what's used
            # is the value used in further mustache templates
            self.rendered_wo_layout = props['body']
            # The page rendered into the page-templates is then
            # rendered into the site layout.
            if not self.metadata['nolayout']:
                props['body'] = pystache.render(self.templates['layout'], props)
            self.rendered_pages[path] = props['body']
        return self.rendered_pages

    # This method goes through all of the steps to completly
    # render a site, and then resets the object the make sure
    # it's good to call again
    def render_site(self):
        self.load_pages()
        self.calculate_properties()
        self.render_pages()
        self.copy_assets()
        self.finalize()
        # The rest of this basically resets the object
        # This was useful before I had the reload_templates method
        # I need to see if it's still necessary
        self.renderable = []
        self.pages = {}
        self.properties = copy.deepcopy(self.original_properties)
        shutil.rmtree(self.rendered_path)
        self.rendered_path = tempfile.mkdtemp()

class GusFSAdapter(Gus):
    def __init__(self, site_dir, dest_dir):
        self.site_dir = site_dir
        self.dest_dir = dest_dir

    def reload_templates(self):
        site_dir = self.site_dir
        dest_dir = self.dest_dir
        super(GusFSAdapter, self).__init__()
        assert os.path.isdir(site_dir), "%s must be a dir" % site_dir
        
        properties_file = os.path.join(site_dir, "properties.yml")
        assert os.path.isfile(properties_file), "%s must be a file" % properties_file
        with open(properties_file, 'r') as f:
            self.properties = yaml.load(f)
        self.original_properties = copy.deepcopy(self.properties)

        assert 'page-types' in self.properties, "'page-types' must be defined in properties.yml"
        self.page_types = self.properties['page-types']
        assert 'date-format' in self.properties, "'date-format' must be defined in properties.yml. See http://docs.python.org/2/library/time.html#time.strftime"
        
        pages_path      = os.path.join(site_dir, "pages")
        assert os.path.isdir(pages_path), "%s must be a dir" % pages_path
        self.pages_path = pages_path

        templates_path  = os.path.join(site_dir, "templates")
        assert os.path.isdir(templates_path), "%s must be a dir" % templates_path
        self.templates_path = templates_path
        
        assets_path     = os.path.join(site_dir, "assets")
        assert os.path.isdir(assets_path), "%s must be a dir" % assets_path
        self.assets_path = assets_path
        
        rendered_path   = dest_dir
        assert os.path.isdir(rendered_path), "%s must be a dir" % rendered_path
        assert os.access(rendered_path, os.W_OK), "%s must be writable" % rendered_path
        self.final_rendered_path = rendered_path
        # Let's not be too destructive right out of the box
        # We'll render into a temp directory and then move it over
        self.rendered_path = tempfile.mkdtemp()
        
        self.path      = {}
        self.templates = { 'indices': {} }

        for page_type, info in self.page_types.items():
            page_path = os.path.join(pages_path, page_type)
            assert os.path.isdir(page_path), "%s must be a dir" % page_path
            self.path[page_type] = page_path

            page_template = os.path.join(templates_path, "%s.mustache" % page_type)
            assert os.path.isfile(page_template), "%s must be a file" % page_template
            with open(page_template, 'r') as f:
                self.templates[page_type] = f.read()
            if 'indices' in info:
                self.templates['indices'][page_type] = {}
                for index_name, index_info in info['indices'].items():
                    page_template = os.path.join(templates_path, "%s-index-%s.mustache" % (page_type, index_name))
                    assert os.path.isfile(page_template), "%s must be a file" % page_template
                    with open(page_template, 'r') as f:
                        self.templates['indices'][page_type][index_name] = f.read()

        layout_template = os.path.join(templates_path, "layout.mustache")
        assert os.path.isfile(layout_template), "%s must be a file" % layout_template
        with open(layout_template, 'r') as f:
            self.templates['layout'] = f.read()

    def render_pages(self):
        for rend in self.renderable:
            # Remove that first character from rend.name because it's a /
            dest_file = os.path.join(self.rendered_path, rend.name[1:] + ".html")
            dest_file_dir = os.path.dirname(dest_file)
            if not os.path.isdir(dest_file_dir):
                os.makedirs(dest_file_dir)
            with open(dest_file, 'w+') as f:
                f.write(rend.render());

    # This method loads all of the pages into memory
    def load_pages(self):
        self.reload_templates()
        for page_type, info in self.page_types.items():
            base_name = self.path[page_type]
            for dirname, dirnames, filenames in os.walk(base_name):
                for filename in filenames:
                    if filename == '.gitignore':
                        continue
                    if re.match("^\..*.sw.$", filename):
                        continue
                    if re.match(".*~$", filename):
                        continue
                    filename = os.path.join(dirname, filename)
                    rel_path = re.sub(base_name, '', filename)
                    rel_path = re.sub("^%s" % os.path.sep, '', rel_path)
                    name, markup_format = os.path.splitext(rel_path)
                    name = self.get_page_path(page_type, name)
                    content = None
                    with open(filename, 'r') as f:
                        content = f.read()
                    print "renderable %s" % name
                    r = Renderable(
                        name,
                        self.templates[page_type],
                        self.templates['layout'],
                        markup_format,
                        content,
                        self.properties,
                        page_type
                    )
                    self.renderable.append(r)

    # This is the eq of doing cp -r directory/* other-dir
    # It copies everything in a directory, but not the directory
    def copytree_wo_root(self, src, dest):
        for dirname, dirnames, filenames in os.walk(src):
            rel_path = re.sub(src, '', dirname)
            rel_path = re.sub("^%s" % os.path.sep, '', rel_path)
            for name in filenames:
                if name == '.gitignore':
                    continue 
                src_name  = os.path.join(dirname, name)
                dest_name = os.path.join(dest, rel_path, name)
                dest_path = os.path.dirname(dest_name)
                if os.path.exists(dest_name):
                    os.unlink(dest_name)
                if not os.path.isdir(dest_path):
                    os.makedirs(dest_path)
                print "%s -> %s" % (src_name, dest_name)
                shutil.copy(src_name, dest_name)
    def copy_assets(self):
        self.copytree_wo_root(self.assets_path, self.rendered_path)

    # Up until now we've been writing to a tmp folder
    # This moves the files from the tmp folder to the real rendered location
    # It then removes the tmp folder and sets up another one for use if we render again
    def finalize(self):
        self.copytree_wo_root(self.rendered_path, self.final_rendered_path)

