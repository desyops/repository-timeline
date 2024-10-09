#!/usr/bin/python3

import os
import subprocess

from timeline import timeline

usage_msg = """

%prog [options] REPOSITORY_LOCATION/SNAPSHOT

    example: %prog /srv/repo/linux/ubuntu.timeline/2015.02.12-141326
"""

from optparse import OptionParser

parser = OptionParser( usage=usage_msg, version="%prog 1.0" )
#parser.add_option('-v', '--verbose', '--debug', action='store_true', dest='verbose', help='run in debug mode')

(opts, args) = parser.parse_args()
options = vars(opts)

if len(args) != 1:
    parser.error('incorrect number of arguments (-h for help)')

snapshot_path = os.path.normpath( args[0] )
split_path = os.path.split( snapshot_path )

t = timeline.Timeline.load( split_path[0] )

try:
    t.delete_snapshot( snapshot=split_path[1] )
except:
    # handle named snapshots
    if os.path.isdir( snapshot_path ):
        subprocess.check_call(['rm', '-rf', snapshot_path ])
        print('deleted unreferenced snapshot [{0}]'.format( snapshot_path ))
    else:
        print('WARNING: TRYING TO DELETE NON-EXISTING SNAPSHOT [{0}]'.format( snapshot_path ))
        raise
