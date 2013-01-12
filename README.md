GUS is a textile and mustache static-site generator.

GUS takes textile files, puts them into a type-specific template, and then places that all into a site-wide layout template.

Run the example by `./gus site:rendered`

Run the example by `./gus -w site:rendered` and as you make changes, the site will be rerendered

# What Gus assumes

Gus assumes that there are 3 directories in your site folder:

* assets
* pages
* templates

and two files

* properties.yml
* templates/layout.mustache

the contents of properties.yml is visible too the mustache templates.

Gus also assumes that there is a `page-types` entry in properties.yml. Beneath `page-types` are the list of pages and their associated output directories.

```yaml
page-types:
   posts:
      web-directory: /posts
      indices:
         tags: 
            over:
               - tags
            web-directory: /posts/tags
         date:
            over:
               - date-year
               - date-month
               - date-day
            web-directory: /posts/by-date
   top-level:
      web-directory: /
```

Indexes generated from metadata can be specified here too. `web-directory` is the directory the index will be placed in, named after `over`. For instances, all posts with a tag of "idea" will be placed in /posts/tags/idea according to the above.  Composite indices, date in the above example, have an "over" specified by an array as opposed to a single field. If more than one field is specified, then indexes are created for each "layer". For instance, in the above example a /2013.html will be created, a /2013/01.html and a /2013/01/11.html will be created.  Each has the pages that match the criteria.

Eventually post-processing (e.g. minification) will also be able to be specified in this structure.

For each type listed, there is assumed to be a folder of the same name in pages/ and a file of the same name in templates/. Each index has a template named "(page-type)-index-(index-name).mustache".

# Format for pages
Lines beginning with % are metadata lines (and get removed from the rendered output). See the next section for more details.

After lines begining with % are removed, the file is run through a markdown to HTML generator as one of:

* Textile, for textile extentions
* Markdown, for md extentions
* nothing, for anything else

After this, the pages are put into a page template, which is what is shown if the page contents are shown elsewhere, like the / page.

The page, rendered in the page template, is then put into the layout.mustache file, which is used when writing the rendered page to a file

## Metadata
Metadata lines have the format of
`(start of line)%key(space)value with possible spaces(end of line)`
Some default keys are

* title
* date
* tags (space separated)
* private (won't show page in indexes)

The keys are available in the mustache environment when render both the page and layout.

# Misc
In the misc folder are apache and nginx configs for a bare site as well as a git post-update hook. These should help get you started towards getting a server up and going.  Mind you, please read these files carefully and audit them and your server's security yourself.
