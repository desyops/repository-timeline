#!/usr/bin/env python2

from mrepo import timeline

import os

usage_msg = """

%prog [options] REPOSITORY_LOCATION/LINK

    examples:

        %prog /path/to/backups/epel/epel.frozen
        %prog /path/to/backups/epel/epel.frozen --snapshot=2015.02.12-141326
"""

from optparse import OptionParser
parser = OptionParser( usage=usage_msg, version="%prog 1.0" )
parser.add_option('--snapshot', help='snapshot to which the link should point', default=None)
#parser.add_option('-v', '--verbose', '--debug', action='store_true', dest='verbose', help='run in debug mode')

(opts, args) = parser.parse_args()
options = vars(opts)

if len(args) != 1:
    parser.error('incorrect number of arguments (-h for help)')

split_path = os.path.split( os.path.normpath(  args[0] ))

t = timeline.Timeline.load( split_path[0] )

t.update_link( link=split_path[1], snapshot=options['snapshot'] )

