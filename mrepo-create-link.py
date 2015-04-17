#!/usr/bin/env python2

from mrepo import timeline

import os

usage_msg = """

%prog [options] REPOSITORY_LOCATION LINKNAME`

    examples:

        %prog /path/to/backups/epel myepel.link
        %prog /path/to/backups/epel myepel.offset7 --max-offset=7
        %prog /path/to/backups/epel myepel.offset7 --snapshot=2015.02.12-141326 --max-offset=7
"""

from optparse import OptionParser
parser = OptionParser( usage=usage_msg, version="%prog 1.0" )
parser.add_option('--max-offset', help='make the link stay pinned to the snapshot with the given offset', type='int', default=0)
parser.add_option('--snapshot', help='snapshot to which the link should point', default=None)
#parser.add_option('-v', '--verbose', '--debug', action='store_true', dest='verbose', help='run in debug mode')

(opts, args) = parser.parse_args()
options = vars(opts)

if len(args) != 2:
    parser.error('incorrect number of arguments (-h for help)')

t = timeline.Timeline.load( args[0] )
t.create_link( link=args[1], snapshot=options['snapshot'], max_offset=options['max_offset'] )

