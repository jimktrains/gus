import os
import shutil
import copy
import pystache
from textile import textile
import yaml
from optparse import OptionParser
import re

parser = OptionParser()
parser.add_option("-d", "--dir", dest="site_dir",
	help="DIR the site resides in", metavar="DIR")
parser.add_option("-v", "--verbose", dest="verbose",
	help="Be verbose")

(options, args) = parser.parse_args()
assert os.path.isdir(options.site_dir), "%s must be a dir" % options.site_dir

print "Rendering the site located in `%s`" % options.site_dir

properties_file = os.path.join(options.site_dir, "properties.yml")
assert os.path.isfile(properties_file), "%s must be a file" % properties_file
with open(properties_file, 'r') as f:
	properties = yaml.load(f)

pages_path      = os.path.join(options.site_dir, "pages")
assert os.path.isdir(pages_path), "%s must be a dir" % pages_path

assets_path     = os.path.join(options.site_dir, "assets")
assert os.path.isdir(assets_path), "%s must be a dir" % assets_path

rendered_path   = os.path.join(options.site_dir, "rendered")
assert os.path.isdir(rendered_path), "%s must be a dir" % rendered_path
assert os.access(rendered_path, os.W_OK), "%s must be writable" % rendered_path

posts_path      = os.path.join(pages_path, "posts")
assert os.path.isdir(posts_path), "%s must be a dir" % posts_path

tl_path         = os.path.join(pages_path, "top-level")
assert os.path.isdir(tl_path), "%s must be a dir" % tl_path

templates_path  = os.path.join(options.site_dir, "templates")
assert os.path.isdir(templates_path), "%s must be a dir" % templates_path

layout_template = os.path.join(templates_path, "layout.mustache")
assert os.path.isfile(layout_template), "%s must be a file" % layout_template
with open(layout_template, 'r') as f:
	layout_template = f.read()

posts_template  = os.path.join(templates_path, "post.mustache")
assert os.path.isfile(posts_template), "%s must be a file" % posts_template
with open(posts_template, 'r') as f:
	posts_template = f.read()

tl_template     = os.path.join(templates_path, "top-level.mustache")
assert os.path.isfile(tl_template), "%s must be a file" % tl_template
with open(tl_template, 'r') as f:
	tl_template = f.read()

index_template  = os.path.join(templates_path, "index.mustache")
assert os.path.isfile(index_template), "%s must be a file" % index_template
with open(index_template, 'r') as f:
	index_template = f.read()

for dirname, dirnames, filenames in os.walk(options.site_dir):
	for subdirname in dirnames:
		pass
	for filename in filenames:
		file_name = os.path.join(dirname, filename)
		rel_file = re.sub(options.site_dir + os.sep, '', file_name)
		if re.match( '.*textile$', file_name):
			print "Rendering file %s" % file_name
			rel_file = re.sub('\.textile', '', rel_file)
			with open(file_name) as f:
				post_raw = f.read()
			post_rendered = textile(re.sub('^\%.*$', '', post_raw, 0, re.MULTILINE))
			meta = re.finditer( '^%(\S*) (.*)$', post_raw, re.MULTILINE)
			props = copy.deepcopy(properties)
			props['post'] = {}
			for match in meta:
				name = match.group(1)
				val  = match.group(2)
				if name == 'tags':
					val = val.split(' ')
				props['post'][name] = val
				props[name] = val
			props['post']['body'] = post_rendered
			print props['post']
			assert 'title' in props['post'], "A post tile must be defined"
			#post_file = copy.copy(props['post']['title'])
			#post_file = re.sub('[^A-Za-z0-9-]', '-', post_file)
			props['body'] = pystache.render(posts_template, props['post'])
			post_layout = pystache.render(layout_template, props)
			post_file = rel_file + ".html"
			post_file = os.path.join(rendered_path, post_file)
			post_dir  = os.path.dirname(post_file)
			if not os.path.isdir(post_dir):
				os.makedirs(post_dir)
			with open(post_file, 'w+') as f:
				f.write(post_layout);
print "Moving assets"

for name in os.listdir(assets_path):
	shutil.copytree(os.path.join(assets_path, name), os.path.join(rendered_path, name))
