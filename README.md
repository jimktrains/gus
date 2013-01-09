GUS is a textile and mustache static-site generator.

GUS takes textile files, puts them into a type-specific template, and then places that all into a site-wide layout template.

Run the example by `./gus -s site -d site/rendered`

Implemented:

* /templates/layout.mustache
* 	/templates/articles.mustache
* 		/pages/articles/<name>.textile -> /<name>.html (name may contain a subdir)
* /templates/layout.mustache
* 	/templates/top-level.mustache
* 		/pages/top-level/<name>.textile -> /<name> (name may contain subdir)
properties.yml -> not rendered to anything
/assets/<name> -> /<name> (may contain subdir)

To be implemented:

* /templates/search.mustache -> /search
* /templates/search-results.mustache -> /search?q=<query>

The compile script needs to do a few things:

1. Create all the pages for the site and place them in a `rendered` directory
1. Create the datafile file for text
1. Create the datafile file for tags
1. Create the datafile file for titles

#Format for articles
Lines begining with % are metadata lines.

Metadata lines have the format of
`(start of line)%key(space)value with possible spaces(end of line)`
Some default keys are

* title
* date
* tags (space seperated)
