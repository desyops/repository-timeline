#!/usr/bin/env python2

from mrepo import timeline

usage_msg = """

%prog [options] REPOSITORY_LOCATION

    examples:

        %prog /path/to/backups/epel/ --freeze
        %prog /path/to/backups/epel/ --consistency-check
        %prog /path/to/backups/epel/ --max-snapshots=90
"""

from optparse import OptionParser
parser = OptionParser( usage=usage_msg, version="%prog 1.0" )
parser.add_option('--max-snapshots', help='change the max. amount of snapshots', type='int')
parser.add_option('--freeze', action='store_true', help='freeze the timeline')
parser.add_option('--unfreeze', action='store_true', help='unfreeze the timeline')
parser.add_option('--consistency-check', action='store_true', help='check repository for consistency')
parser.add_option('-v', '--verbose', '--debug', action='store_true', dest='verbose', help='run in debug mode')

(opts, args) = parser.parse_args()
options = vars(opts)

if len(args) != 1:
    parser.error('incorrect number of arguments (-h for help)')

t = timeline.Timeline.load( args[0] )

if options['max_snapshots']:
    t.set_max_snapshots( options['max_snapshots'] )
    t.rotate_snapshots()

if options['freeze']:
    t.freeze()

if options['unfreeze']:
    t.unfreeze()

if options['consistency_check']:
    t.consistency_check()

if options['verbose']:
    print t

t.save()
