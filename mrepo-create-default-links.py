#!/usr/bin/env python2

from mrepo import timeline

import os

usage_msg = """

%prog [options] REPOSITORY_LOCATION`

    examples:

        %prog /path/to/backups/epel
"""

from optparse import OptionParser
parser = OptionParser( usage=usage_msg, version="%prog 1.0" )
#parser.add_option('-v', '--verbose', '--debug', action='store_true', dest='verbose', help='run in debug mode')

(opts, args) = parser.parse_args()
options = vars(opts)

if len(args) != 1:
    parser.error('incorrect number of arguments (-h for help)')

t = timeline.Timeline.load( args[0] )
t.create_link( 'upstream', max_offset=1 )
t.create_link( 'downstream' )
for i in (3,7,14,21,30,60,90):
    if t.get_max_snapshots() >= i:
        t.create_link( 'offset{0}'.format(str(i).zfill(3)), max_offset=i )
