#!/usr/bin/env python2

from timeline import timeline

usage_msg = """

%prog [options] REPOSITORY_LOCATION

    examples:

        %prog /srv/repo/linux/ubuntu.timeline --freeze
        %prog /srv/repo/linux/ubuntu.timeline --unfreeze
        %prog /srv/repo/linux/ubuntu.timeline --consistency-check
        %prog /srv/repo/linux/ubuntu.timeline --max-snapshots=42
"""

from optparse import OptionParser
parser = OptionParser( usage=usage_msg, version="%prog 1.0" )
parser.add_option('--max-snapshots', help='change the max. amount of snapshots', type='int')
parser.add_option('--excludes', help='change the list of excludes', default=None)
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

# we need to use None here since user might want to clean the excludes value by using --excludes=''
if options['excludes'] is not None:
    t.set_excludes( options['excludes'] )

if options['freeze']:
    t.freeze()

if options['unfreeze']:
    t.unfreeze()

if options['consistency_check']:
    t.consistency_check()

if options['verbose']:
    print t

t.save()
