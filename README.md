GUS is a textile and mustache static-site generator.

GUS takes textile files, puts them into a type-specific template, and then places that all into a site-wide layout template.

Run the example by `./gus site:rendered`

Run the example by `./gus -w site:rendered` and as you make changes, the site will be rerendered

# Implemented

* `/templates/layout.mustache` + `/templates/articles.mustache` + `/pages/articles/<name>.textile` -> /`<name>`.html (name may contain a subdir)
* `/templates/layout.mustache` + `/templates/top-level.mustache` + `/pages/top-level/<name>.textile` -> /`<name>`.html (name may contain subdir)
* properties.yml -> not rendered to anything
* /assets/`<name>` -> /`<name>` (may contain subdir)

# To be implemented

* /templates/search.mustache -> /search
* /templates/search-results.mustache -> /search?q=<query>
 * Will require pre-computing statistics and indexes

# Format for articles
Lines beginning with % are metadata lines (and get removed from the rendered output).

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

# What Gus assumes

Gus assumes that there are 3 directories in your site folder:

* assets
* pages
* templates

and one file

* properties.yml

the contents of properties.yml is visible too the mustache templates.

Gus also assumes that there is a `page-types` entry in properties.yml. Beneath `page-types` are the list of pages and their associated output directories.

```yaml
page-types:
   posts:
      web-directory: /posts
   top-level:
      web-directory: /
```

eventually post-processing (e.g. minification) will also be able to be specified in this structure.

For each type listed, there is assumed to be a folder of the same name in pages/ and a file of the same name in templates/.

There is also assumed to be a file called templates/layout.mustache that is used as the main site layout.
