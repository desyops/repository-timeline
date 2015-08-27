#!/usr/bin/env python2

from timeline import timeline
import os, sys

usage_msg = """

%prog [options] REPOSITORY_LOCATION

    example: %prog /srv/repo/linux/ubuntu.timeline
"""

from optparse import OptionParser
parser = OptionParser( usage=usage_msg, version="%prog 1.0" )
parser.add_option('--random-sleep', help='sleep a random amount of seconds [default=%default] before taking snapshot', type='int', default=None)
parser.add_option('--sleep-after', help='sleep the given amount of seconds after taking the snapshot', type='int', default=None)
parser.add_option('--lock', action='store_true', help='use lockfile to protect against creating concurrent snapshots' )
parser.add_option('-v', '--verbose', '--debug', action='store_true', dest='verbose', help='run in debug mode')

(opts, args) = parser.parse_args()
options = vars(opts)

if len(args) != 1:
    parser.error('incorrect number of arguments (-h for help)')

if options['lock']:

    try:
        import lockfile
    except ImportError:
        from timeline import lockfile

    lock_file = os.path.join( args[0], '.lock' )
    lock = lockfile.FileLock( lock_file )

    try:
        lock.acquire( timeout=1 )
    except:
        if options['verbose']:
            print 'lockfile [{0}] already locked'.format( lock_file )
        sys.exit(0)

try:
    t = timeline.Timeline.load( args[0] )
    t.create_snapshot( random_sleep_before_snapshot=options['random_sleep'], sleep_after_snapshot=options['sleep_after'])
except:
    if options['lock']:
        lock.release()
    raise

if options['lock']:
    lock.release()
