GUS is a textile and mustache static-site generator.

GUS takes textile files, puts them into a type-specific template, and then places that all into a site-wide layout template.

types are: posts and top-level pages.

How I want this to render:

/templates/404.mustache
/templates/articles.mustache
  /pages/articles/<name>.textile -> /articles/<year>/<month>/<day>/<name>
/templates/index.mustache -> /
/templates/layout.mustache
/templates/search.mustache -> /search
/templates/search-results.mustache -> /search?q=<query>
/templates/top-level.mustache
  /pages/top-level/<name>.textile -> /<name>
properties.yml
/assets/css -> .tld/css
/assets/js -> .tld/js
/assets/img -> .tld/img

The compile script needs to do a few things:
1. Create all the pages for the site 
   and place them in a `rendered` directory
2. Create the datafile file for text
3. Create the datafile file for tags
4. Create the datafile file for titles

Format for articles
Lines begining with % are metadata lines
Metadata lines have the format of
(start of line)%key(space)value with possible spaces(end of line)
Some default keys are
 * title
 * date
 * tags (space seperated)
