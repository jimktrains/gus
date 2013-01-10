#!/usr/bin/env python

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
	def __init__(self, name, page_template, layout_template, markup_format, content, properties, page_type):
		self.name = name
		self.page_template = page_template
		self.markup_format = markup_format
		self.content = content
		self.properties = properties
		self.rendered = False
		self.rendered_wo_layout = False
		self.page_type = page_type
		self.metadata = False
		self.layout_template = layout_template
		self.extract_metadata()
		self.render()
	def as_dict(self):
		return {
			"name"     : self.name,
			"title"    : self.metadata['title'],
			"date"     : self.metadata['date'],
			"tags"     : self.metadata['tags'],
			"content"  : self.rendered_wo_layout,
			"metadata" : self.metadata
		}
	def extract_metadata(self):
		if not self.metadata:
			meta = re.finditer( '^%(\S*) (.*)$', self.content, re.MULTILINE)
			props = {}
			for match in meta:
				name = match.group(1)
				val  = match.group(2)
				if name == 'tags':
					val = val.split(' ')
				props[name] = val
			if not 'title' in props:
				props['title'] = self.name
			if not 'date' in props:
				props['date'] = None
			if not 'tags' in props:
				props['tags'] = []
			else:
				props['tags'] = [ {"tag": x} for x in props['tags']]
			props['name'] = self.name
			self.metadata = props
		return self.metadata
	def render(self):
		if True: #not self.rendered and false:
			page_rendered = re.sub('^\%.*$', '', self.content, 0, re.MULTILINE)
			if self.markup_format == ".textile":
				page_rendered = textile(page_rendered)
			elif self.markup_format == ".md":
				page_rendered = markdown(page_rendered)

			props = dict(self.metadata.items() + self.properties.items())

			props['body'] = page_rendered
			props['body'] = pystache.render(self.page_template, props)
			# This step is done incase self.content has markup in it
			props['body'] = pystache.render(props['body'], props)
			self.rendered_wo_layout = props['body']
			props['body'] = pystache.render(self.layout_template, props)
			self.rendered = props['body']
		return self.rendered


class Gus(object):
	def __init__(self):
		self.renderable = []
		self.pages = {}
		self.page_types = {
			"posts": {
				"final_path": 'posts'
			},
			"top-level": {
				"final_path": ''
			}
		}

	# This needs a better name
	# basically it calculates all the lists of all the pages
	# and tags and everything else we need
	# Later on it'll calculate rf-idf and tag clouds and the such
	def calculate_properties(self):
		self.properties['current_time'] = time.time();
		for page_type, info in self.page_types.items():
			# Sort the pages by date
			self.pages[page_type] = [ x for x in self.renderable if x.page_type == page_type ]
			self.pages[page_type].sort( key = lambda page : page.metadata['date'], reverse=True)

			# Allow the templates to see all the pages
			self.properties[page_type] = [ x.as_dict() for x in self.pages[page_type] ]
			self.properties["last_5_%s" % page_type] = [ x.as_dict() for x in self.pages[page_type][:5] ]

			# Allow the templates to get a list of tags and associated pages
			tags = set([ tag['tag'] for page in self.pages[page_type] for tag in page.metadata['tags'] ] )
			self.properties["%s_tags" % page_type] = []
			for tag in tags:
				self.properties["%s_tags" % page_type].append({
					'tag':      tag,
					'pages': [ x.as_dict() for x in self.pages[page_type] if tag in x.metadata['tags'] ]
				})

	def get_web_path(self, page_type, name):
		return os.path.sep + os.path.join(self.page_types[page_type]['final_path'], name)

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
		
		pages_path      = os.path.join(site_dir, "pages")
		assert os.path.isdir(pages_path), "%s must be a dir" % pages_path
		self.pages_path = pages_path
		
		assets_path     = os.path.join(site_dir, "assets")
		assert os.path.isdir(assets_path), "%s must be a dir" % assets_path
		self.assets_path = assets_path
		
		rendered_path   = dest_dir
		assert os.path.isdir(rendered_path), "%s must be a dir" % rendered_path
		assert os.access(rendered_path, os.W_OK), "%s must be writable" % rendered_path
		self.final_rendered_path = rendered_path
		self.rendered_path = tempfile.mkdtemp()
		
		self.path = {}
		posts_path      = os.path.join(pages_path, "posts")
		assert os.path.isdir(posts_path), "%s must be a dir" % posts_path
		self.path['posts'] = posts_path
		
		top_level_path         = os.path.join(pages_path, "top-level")
		assert os.path.isdir(top_level_path), "%s must be a dir" % top_level_path
		self.path['top-level'] = top_level_path
		
		templates_path  = os.path.join(site_dir, "templates")
		assert os.path.isdir(templates_path), "%s must be a dir" % templates_path
		self.templates_path = templates_path

		self.templates = {}
		layout_template = os.path.join(templates_path, "layout.mustache")
		assert os.path.isfile(layout_template), "%s must be a file" % layout_template
		with open(layout_template, 'r') as f:
			self.templates['layout'] = f.read()
		
		posts_template  = os.path.join(templates_path, "post.mustache")
		assert os.path.isfile(posts_template), "%s must be a file" % posts_template
		with open(posts_template, 'r') as f:
			self.templates['posts'] = f.read()
		
		top_level_template     = os.path.join(templates_path, "top-level.mustache")
		assert os.path.isfile(top_level_template), "%s must be a file" % top_level_template
		with open(top_level_template, 'r') as f:
			self.templates['top-level'] = f.read()

	def render_pages(self):
		for rend in self.renderable:
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
					name = self.get_web_path(page_type, name)
					content = None
					with open(filename, 'r') as f:
						content = f.read()
					print "renderable %s" % name
					r = Renderable(name, self.templates[page_type], self.templates['layout'], markup_format, content, self.properties, page_type)
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

