#!/usr/bin/env python2

from mrepo import timeline

import os

usage_msg = """

%prog [options] REPOSITORY_LOCATION/SNAPSHOT_NAME`

    creates a new snapshot which is not kept, stored or managed within the timeline metadata.

    this snapshots are completely independent of the timeline snapshots and can be altered or
    deleted with a simple rm -rf ...

    examples:

        %prog /path/to/backups/epel/myepel
        %prog /path/to/backups/epel/myepel --lock --snapshot=2015.02.12-141326
"""

from optparse import OptionParser
parser = OptionParser( usage=usage_msg, version="%prog 1.0" )
parser.add_option('--source-snapshot', help='source snapshot from where to create the new snapshot', default=None)
parser.add_option('--lock', action='store_true', help='use lockfile to protect against creating concurrent snapshots' )
#parser.add_option('-v', '--verbose', '--debug', action='store_true', dest='verbose', help='run in debug mode')

(opts, args) = parser.parse_args()
options = vars(opts)

if len(args) != 1:
    parser.error('incorrect number of arguments (-h for help)')

split_path = os.path.split( os.path.normpath( args[0] ))

if '/' in options['source_snapshot']:
    options['source_snapshot'] = os.path.split( os.path.normpath( options['source_snapshot'] ))[1]

if options['lock']:

    try:
        import lockfile
    except ImportError:
        from mrepo import lockfile

    lock_file = os.path.join( split_path[0], '.lock' )
    lock = lockfile.FileLock( lock_file )

    try:
        lock.acquire( timeout=1 )
    except:
        if options['verbose']:
            print 'lockfile [{0}] already locked'.format( lock_file )
        sys.exit(0)

try:
    t = timeline.Timeline.load( split_path[0] )
    t.create_named_snapshot( snapshot=split_path[1], source_snapshot=options['source_snapshot'] )
except:
    if options['lock']:
        lock.release()
    raise

if options['lock']:
    lock.release()

