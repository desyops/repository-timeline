#!/usr/bin/env python2

from timeline import timeline

import os

usage_msg = """

%prog [options] REPOSITORY_LOCATION/LINK NEW_LINKNAME`

    examples:

        %prog /path/to/backups/epel/myepel.link new_epel.link
"""

from optparse import OptionParser
parser = OptionParser( usage=usage_msg, version="%prog 1.0" )
#parser.add_option('-v', '--verbose', '--debug', action='store_true', dest='verbose', help='run in debug mode')

(opts, args) = parser.parse_args()
options = vars(opts)

if len(args) != 2:
    parser.error('incorrect number of arguments (-h for help)')

split_path = os.path.split( os.path.normpath( args[0] ))

link_name = args[1]
if '/' in args[1]:
    link_name = os.path.split( os.path.normpath( args[1] ))[1]

t = timeline.Timeline.load( split_path[0] )
l = t.delete_link( link=split_path[1] )
t.create_link( link=link_name, snapshot=l['snapshot'], max_offset=l['max_offset'], warn_before_max_offset=l['warn_before_max_offset'] )

