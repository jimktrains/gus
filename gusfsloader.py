#!/usr/bin/env python

import copy
import os
import re
import shutil
import tempfile
import yaml

class GusFSLoader(object):
    def __init__(self, site_dir, dest_dir, gus):
        self.site_dir = site_dir
        self.dest_dir = dest_dir
        self.gus      = gus

    def reload_templates(self):
        site_dir = self.site_dir
        dest_dir = self.dest_dir
        super(GusFSLoader, self).__init__()
        assert os.path.isdir(site_dir), "%s must be a dir" % site_dir

        properties_file = os.path.join(site_dir, "properties.yml")
        assert os.path.isfile(properties_file), "%s must be a file" % properties_file
        with open(properties_file, 'r') as f:
            self.properties = yaml.load(f)
        self.original_properties = copy.deepcopy(self.properties)

        assert 'page-types' in self.properties, "'page-types' must be defined in properties.yml"
        self.page_types = self.properties['page-types']
        assert 'date-format' in self.properties, "'date-format' must be defined in properties.yml. See http://docs.python.org/2/library/time.html#time.strftime"
        self.gus.properties = self.properties
        self.gus.page_types = self.page_types

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
                self.gus.set_page_template(page_type, f.read())
            if 'indices' in info:
                self.templates['indices'][page_type] = {}
                for index_name, index_info in info['indices'].items():
                    page_template = os.path.join(templates_path, "%s-index-%s.mustache" % (page_type, index_name))
                    assert os.path.isfile(page_template), "%s must be a file" % page_template
                    with open(page_template, 'r') as f:
                        self.gus.set_index_template(page_type, index_name, f.read())

        layout_template = os.path.join(templates_path, "layout.mustache")
        assert os.path.isfile(layout_template), "%s must be a file" % layout_template
        with open(layout_template, 'r') as f:
            self.gus.set_site_template(f.read())

    def render_pages(self):
        for page_path, page_contents in self.gus.render_renderables().items():
            # Remove that first character from rend.name because it's a /
            dest_file = os.path.join(self.rendered_path, page_path[1:] + ".html")
            dest_file_dir = os.path.dirname(dest_file)
            if not os.path.isdir(dest_file_dir):
                os.makedirs(dest_file_dir)
            with open(dest_file, 'w+') as f:
                f.write(page_contents[0]);

    # This method loads all of the pages into memory
    def load_pages(self):
        self.reload_templates()
        for page_type, info in self.page_types.items():
            base_name = self.path[page_type]
            for dirname, dirnames, filenames in os.walk(base_name):
                for filename in filenames:
                    # Ignore vim and emacs swap files
                    # as well as .gitignore
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
                    name = self.gus.get_page_path(page_type, name)
                    content = None
                    with open(filename, 'r') as f:
                        content = f.read()
                    print "renderable %s" % name
                    self.gus.add_page(page_type, name, content, markup_format);

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

    # This method goes through all of the steps to completly
    # render a site, and then resets the object the make sure
    # it's good to call again
    def render_site(self):
        self.load_pages()
        self.gus.calculate_properties()
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
