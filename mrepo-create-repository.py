#!/usr/bin/env python2

from mrepo import timeline

usage_msg = """

%prog [options] NAME SOURCE DESTINATION

    example: %prog epel /path/to/mirrors/epel /path/to/backups/epel/
"""

from optparse import OptionParser
parser = OptionParser( usage=usage_msg, version="%prog 1.0" )
parser.add_option('-i', '--initialize', action='store_true', help='initialize repository')
#parser.add_option('-v', '--verbose', '--debug', action='store_true', dest='verbose', help='run in debug mode')

(opts, args) = parser.parse_args()
options = vars(opts)

if len(args) < 3:
    parser.error('incorrect number of arguments (-h for help)')

t = timeline.Timeline( *args )

if options['initialize']:
    t.create_snapshot()
    t.create_link( 'upstream', max_offset=1 )
    for i in (3,7,14,21,30,60,90):
        t.create_link( 'offset{0}'.format(str(i).zfill(3)), max_offset=i )

t.save()

