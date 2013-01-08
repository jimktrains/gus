# This script needs to do a few things:
# 1. Create all the pages for the site 
#    and place them in a `rendered` directory
# 2. Create the lsiData.pkl file (with full SVD) for text
# 3. Create the lsiData.pkl file (with full SVD) for tags
# 4. Create the lsiData.pkl file (with full SVD) for titles

# Format for articles
# Lines begining with % are metadata lines
# Metadata lines have the format of
# (start of line)key: value(end of line)
# Some default keys are
#  * title
#  * date
#  * tags
#  * comments (on/off)
#
#
#  metadata lines must come first
#  flowed by an empty line
#  article body as textile
