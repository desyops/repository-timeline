#!/usr/bin/python3

import os

from timeline import timeline

usage_msg = """

%prog [options] REPOSITORY_LOCATION/LINKNAME`

    examples:

        %prog /srv/repo/linux/ubuntu.timeline/myrepo.link
        %prog /srv/repo/linux/ubuntu.timeline/myrepo.offset7 --max-offset=7
        %prog /srv/repo/linux/ubuntu.timeline/myrepo.offset7 --snapshot=2015.02.12-141326 --max-offset=7
"""

from optparse import OptionParser

parser = OptionParser( usage=usage_msg, version="%prog 1.0" )
parser.add_option('--max-offset', help='make the link stay pinned to the snapshot with the given offset', type='int', default=0)
parser.add_option('--snapshot', help='snapshot to which the link should point', default=None)
#parser.add_option('-v', '--verbose', '--debug', action='store_true', dest='verbose', help='run in debug mode')

(opts, args) = parser.parse_args()
options = vars(opts)

if len(args) != 1:
    parser.error('incorrect number of arguments (-h for help)')

split_path = os.path.split( os.path.normpath( args[0] ))

if options['snapshot'] and '/' in options['snapshot']:
    options['snapshot'] = os.path.split( os.path.normpath( options['snapshot'] ))[1]

t = timeline.Timeline.load( split_path[0] )
t.create_link( link=split_path[1], snapshot=options['snapshot'], max_offset=options['max_offset'] )

