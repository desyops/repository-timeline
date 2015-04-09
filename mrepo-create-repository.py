#!/usr/bin/env python2

from mrepo import timeline

usage_msg = """

%prog [options] NAME SOURCE DESTINATION

    examples:

        %prog epel /path/to/mirrors/epel /path/to/backups/epel/
        %prog epel /path/to/mirrors/epel /path/to/backups/epel/ --max-snapshots=90
"""

from optparse import OptionParser
parser = OptionParser( usage=usage_msg, version="%prog 1.0" )
parser.add_option('-m', '--max-snapshots', help='default [%default]', type='int', default=30)
parser.add_option('-i', '--initialize', action='store_true', help='initialize repository')
#parser.add_option('-v', '--verbose', '--debug', action='store_true', dest='verbose', help='run in debug mode')

(opts, args) = parser.parse_args()
options = vars(opts)

if len(args) < 3:
    parser.error('incorrect number of arguments (-h for help)')


t = timeline.Timeline( *args, max_snapshots=opts.max_snapshots )

if options['initialize']:
    t.create_snapshot()
    t.create_link( 'upstream', max_offset=1 )
    for i in (3,7,14,21,30,60,90):
        if options['max_snapshots'] >= i:
            t.create_link( 'off{0}days'.format(str(i).zfill(3)), max_offset=i )

t.save()

