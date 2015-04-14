#!/usr/bin/env python2

# Author: Jan Engels, DESY - IT

import os, sys, time, random, logging, logging.config, subprocess, pickle, pprint

cwd=os.path.dirname(sys.argv[0])
logging.config.fileConfig( os.path.join( cwd, 'mrepo-logging.cfg' ))

from datetime import datetime


def isalnum( string, allowed_extra_chars='' ):
    """ check if the given string only contains alpha-numeric characters + optionally allowed extra chars """
    
    stripped_name = string.translate( None, allowed_extra_chars )

    return stripped_name.isalnum()


class Timeline:

    logger = logging.getLogger('Timeline')
    _datafile_ext = '.timeline'

    def __init__( self, name, source, destination, max_snapshots=30, excludes='' ):
        """ create a new timeline instance for a given source directory

                ARGUMENTS:

                    name:           the name of the timeline instance
                    source:         the timeline source directory (from where snapshots are taken)
                    destination:    the timeline destination directory (where snapshots are written into)
                    max_snapshots:  the max. amount of snapshots
                    excludes:       colon-separated list of files/directories to exclude when creating snapshots
        """

        self.logger.info( 'configuring timeline [{0}] from source [{1}] into destination [{2}]'.format( name, source, destination ))

        if not isalnum( name, '-_.' ):
            raise Exception( 'name string must only consist of alpha-numeric characters, dots, underscores and dashes' )

        if not os.path.isdir( source ):
            raise Exception( 'source is not a valid directory' )

        if not os.path.exists( destination ):
            os.makedirs( destination )

        self._name = name
        self._source = os.path.normpath( source )
        self._destination = os.path.normpath( destination )
        self.set_max_snapshots( max_snapshots )
        self.set_excludes( excludes )

        # flag to freeze/unfreeze timeline
        self._frozen = False

        # contains all snapshots
        self._snapshots = {}

        # snapshots "timeline" (used for snapshot rotation)
        # new snapshots appended to the end, old snapshots removed from the beginning
        self._lsnapshots = []

        # contains all links
        self._links = {}

        # percistency file for storing the class state
        self._datafile = os.path.join( self._destination, self._datafile_ext )

        # create a logger for the current instance
        self.logger = logging.getLogger('Timeline.{0}'.format( name ))

        # load class state from metadata file in case one exists
        if os.path.exists( self._datafile ):
            self._load_state()
            if (name != self._name
                or os.path.normpath( source) != self._source
                or os.path.normpath( destination ) != self._destination ):
                raise Exception( 'inconsistencies found loading class state from metadata file' )


    @classmethod
    def load( cls, path ):
        """ create a new timeline instance with parameters read from a metadata file in the given path """

        metadata_file = os.path.join( path, Timeline._datafile_ext )

        Timeline.logger.info( 'loading timeline instance from [{0}]'.format( metadata_file ) )
        fh = open( metadata_file, 'r' )
        pickle_data = pickle.load( fh )

        # this calls __init__ with the given arguments loaded from the metadata file
        # the .get() calls are for backwards compatibility, i.e. if the stored object did not contain those values at creation time
        return cls( pickle_data['_name'], pickle_data['_source'], pickle_data['_destination'], pickle_data.get('_max_snapshots', 30), pickle_data.get('_excludes', '') )


    def __str__( self ):
        """ human readable string representation of this class """

        return """

    {0} SNAPSHOTS ({1}) {2}
    
    {3}
    
    
    {4} LINKS ({5}) {6}
    
    {7}
    
    
    {8} SNAPSHOTS TIMELINE {9}
    
    {10}
    
    
    {11} TIMELINE INSTANCE DETAILS {12}
    
    {13}

        """.format( 30*'=', len(self._snapshots), 30*'=', pprint.pformat( self._snapshots ), 32*'=', len(self._links), 32*'=', pprint.pformat( self._links ), 25*'=', 25*'=', self._lsnapshots, 22*'=', 22*'=', repr(self)  )


    def __repr__( self ):
        """ representation of this class """

        return '[name={0}, source={1}, destination={2}, max_snapshots={3}, excludes={4}]'.format( self._name, self._source, self._destination, self._max_snapshots, self.get_excludes() )


    def _load_state( self ):
        """ loads timeline state from file """

        self.logger.info( 'loading timeline state...')
        fh = open( self._datafile, 'r' )
        self.__dict__.update(pickle.load( fh ))
        self.logger.info( 'timeline state loaded from [{0}]'.format( self._datafile ))


    def save( self ):
        """ saves current timeline state into file """

        self.logger.info( 'saving current timeline state...')
        fh = open( self._datafile, 'w' )
        #pickle.dump( self, fh )
        d = self.__dict__.copy() # copy the dict since we will change it
        del d['logger'] # need to delete self.logger due to file object
        pickle.dump( d, fh )
        self.logger.debug( 'current state saved into [{0}]'.format( self._datafile ))


    def set_max_snapshots( self, max_snapshots ):
        """ helper method to set max snapshots value """

        if not max_snapshots in range(3,366):
            raise Exception( 'max_snapshots must be in range 3-366' )

        self._max_snapshots = max_snapshots


    def get_max_snapshots( self ):
        """ helper method to return the max snapshots value """

        return self._max_snapshots


    def set_excludes( self, excludes ):
        """ helper method to set excludes value """

        excludes_clean = []

        if isinstance( excludes, str ):
            excludes_clean = [ i.strip() for i in excludes.split(':') if i ]
        elif isinstance( excludes, list ):
            excludes_clean = excludes
        else:
            raise Exception( 'excludes value must be a colon-separated string or a list' )

        excludes_clean = [ os.path.normpath(i) for i in excludes_clean ]

        for i in excludes_clean:
            if i[0] == '/' or i[:1] == '..' or i == '.' or i == '*':
                raise Exception( 'excludes value must only contain relative paths' )
            exclude_path = os.path.join( self._source, i )
            if not os.path.exists( exclude_path ):
                raise Exception( 'invalid exclude path [{0}]'.format( exclude_path ))

        self._excludes = excludes_clean


    def get_excludes( self ):
        """ helper method to return the excludes value """

        return ':'.join( self._excludes )


    def freeze( self, user='root' ):
        """ freezes the timeline

                no new snapshots are taken until 'unfreeze()' is called

                this method should only be used in emergency situations! 
        """

        if self._frozen:
            raise Exception( 'timeline has already been frozen by user [{0}]'.format( self._frozen ))

        self._frozen = user

        self.logger.info( 'timeline has been frozen')


    def unfreeze( self, user='root' ):
        """ unfreezes the timeline
                opposite to the 'freeze()' method
        """

        self.logger.info( 'timeline has been unfrozen by user []'.format( user ))

        self._frozen = False


    def _snapshot_copy_by_hardlink( self, source_path, snapshot_path ):
        """ helper method which copies (by hard-linking) the given directory """

        #subprocess.check_call(['cp', '-al', source_path, snapshot_path ])

        if not os.path.exists( snapshot_path ):
            os.makedirs( snapshot_path )

        for i in os.listdir( source_path ):
            source_obj = os.path.normpath( os.path.join( source_path, i ))
            for e in self._excludes:
                exclude_obj = os.path.normpath( os.path.join( source_path, e ))
                if source_obj == exclude_obj:
                    self.logger.debug( 'excluding (skipping) object [{0}]'.format( exclude_obj ))
                    break
            else:
                subprocess.check_call(['cp', '-al', source_obj, snapshot_path ])

        # cleanup excludes which are defined as 'subdirectories'
        for e in self._excludes:
            if '/' in e:
                exclude_obj = os.path.normpath( os.path.join( snapshot_path, e ))
                if os.path.exists( exclude_obj ):
                    self.logger.debug( 'excluding (deleting) object [{0}]'.format( exclude_obj ))
                    subprocess.check_call(['rm', '-rf', exclude_obj ])
                else:
                    self.logger.warning( 'trying to exclude (delete) unexisting object [{0}]'.format( exclude_obj ))


    def _snapshot_find_and_copy_objects( self, source_path, snapshot_path ):
        """ helper method which first removes and afterwards copies
            (instead of just hard-linking) a list of files/directories
        """

        # poor man's code to figure out which type of repository...
        distro = 'redhat'
        if os.path.exists( os.path.join( source_path, 'dists' )):
            distro = 'debian'
            if os.path.exists( os.path.join( source_path, 'ubuntu' )):
                distro = 'ubuntu'

        copy_dirs = []
        copy_files = []

        if distro == 'redhat':
            # list of directories which will be copied instead of hard-linked
            #copy_dirs = ['repodata', 'repoview']
            copy_dirs = ['repodata']
        else:
            copy_dirs = ['binary-*']
            copy_files = ['Release', 'Release.gpg', 'Contents-*.gz']

        if copy_dirs:
            # generate a find cmd with list of dirs to be copied
            # e.g. find /tmp/foo -type d -name repodata -o -name repoview -o -name bar
            find_cmd = ['find', snapshot_path, '-type', 'd', '-name', copy_dirs[0]]
            for i in copy_dirs[1:]:
                find_cmd.extend( ['-o', '-name', i] )

            #subprocess.check_output( find_cmd )
            cdirs = subprocess.Popen( find_cmd, stdout=subprocess.PIPE).communicate()[0].split()
            for cdir in cdirs:
                subprocess.check_call(['rm', '-rf', cdir ])
                rel_path = os.path.relpath( cdir, snapshot_path)
                self.logger.debug( 'copying directory [{0}] to [{1}]'.format( os.path.join(source_path, rel_path), cdir ))
                subprocess.check_call(['cp', '-a', os.path.join(source_path, rel_path), cdir ])

        if copy_files:
            # generate a find cmd with list of files to be copied
            # e.g. find /tmp/foo -type f -name Release -o -name Release.gpg ...
            find_cmd = ['find', snapshot_path, '-type', 'f', '-name', copy_files[0]]
            for i in copy_files[1:]:
                find_cmd.extend( ['-o', '-name', i] )

            #subprocess.check_output( find_cmd )
            cfiles = subprocess.Popen( find_cmd, stdout=subprocess.PIPE).communicate()[0].split()
            for cfile in cfiles:
                subprocess.check_call(['rm', '-f', cfile ])
                rel_path = os.path.relpath( cfile, snapshot_path)
                self.logger.debug( 'copying file [{0}] to [{1}]'.format( os.path.join(source_path, rel_path), cfile ))
                subprocess.check_call(['cp', '-a', os.path.join(source_path, rel_path), cfile ])


    def create_named_snapshot( self, snapshot, source_snapshot=None ):
        """ creates a named snapshot from the source directory

                no action is taken if the timeline has been frozen!
        """

        self.logger.info( 'creating new snapshot [{0}]'.format( snapshot ))

        self._check_frozen()

        if source_snapshot:
            self.logger.info( 'using source snapshot [{0}]'.format( source_snapshot ))
            self._valid_snapshot( source_snapshot )
            source_path = self._snapshots[source_snapshot]['path']
        else:
            source_path = self._source

        if not isalnum( snapshot, '-_.' ):
            raise Exception( 'snapshot name must only consist of alpha-numeric characters, dots, underscores and dashes' )

        # create new snapshot
        snapshot_path = os.path.join( self._destination, snapshot )
        self._snapshots[snapshot] = { 'created' : datetime.now(), 'path': snapshot_path, 'links' : [] }
        self.save()

        # make changes in the file system
        self._snapshot_copy_by_hardlink( source_path, snapshot_path )
        self._snapshot_find_and_copy_objects( source_path, snapshot_path )

        self.logger.debug( 'created new snapshot [{0}]'.format( snapshot ))


    def create_snapshot( self, random_sleep_before_snapshot=None, sleep_after_snapshot=None ):
        """ creates a new snapshot from the source directory

                no action is taken if the timeline has been frozen!

                the oldest snapshot is removed when <max_snapshots> is reached
        """

        if random_sleep_before_snapshot:
            sleep_time = random.randint( 1, random_sleep_before_snapshot )
            self.logger.info( 'sleeping [{0}] seconds before taking a new snapshot'.format( sleep_time ))
            time.sleep( sleep_time )

        now = datetime.now()

        snapshot = now.strftime("%Y.%m.%d-%H%M%S")

        # FIXME for debugging only...
        if getattr( self, '_debug', None ):
            snapshot = now.strftime("%Y.%m.%d-%H%M%S.%f")

        self.logger.info( 'creating new snapshot [{0}]'.format( snapshot ))

        self._check_frozen()

        if snapshot in self._lsnapshots:
            raise Exception( 'snapshot [{0}] already exists!'.format( snapshot ))

        # create new snapshot
        snapshot_path = os.path.join( self._destination, snapshot )
        self._snapshots[snapshot] = { 'created' : now, 'path': snapshot_path, 'links' : [] }
        self._lsnapshots.append( snapshot )
        self.save()

        # make changes in the file system
        self._snapshot_copy_by_hardlink( self._source, snapshot_path )
        self._snapshot_find_and_copy_objects( self._source, snapshot_path )

        # delete old snapshots and handle links...
        self.rotate_snapshots()

        self.logger.debug( 'created new snapshot [{0}]'.format( snapshot ))

        if sleep_after_snapshot:
            self.logger.info( 'sleeping for [{0}] seconds'.format( sleep_after_snapshot ))
            time.sleep( sleep_after_snapshot )


    def delete_snapshot( self, snapshot ):
        """ deletes the given snapshot and handles links appropriately
        
                no action is taken if the timeline has been frozen!
        """

        self.logger.info( 'deleting snapshot [{0}]'.format( snapshot ))

        self._check_frozen()
        self._valid_snapshot( snapshot, fail_on_disk_check=False )
        
        # handle links
        snapshot_links = self._snapshots[ snapshot ][ 'links' ][:]
        for link in snapshot_links:
            # if we are deleting the last snapshot we should also delete the links
            if len( self._lsnapshots ) == 1:
                self.delete_link( link )
            else:
                self.update_link( link, self._get_neighbour_snapshot( snapshot ))

        self._lsnapshots.remove( snapshot )
        deleted_snapshot = self._snapshots.pop(snapshot)
        self.save()

        # make changes in the file system
        subprocess.check_call(['rm', '-rf', deleted_snapshot['path'] ])

        self.logger.debug( 'deleted snapshot [{0}] [{1}]'.format( snapshot, deleted_snapshot ))


    def create_link( self, link, snapshot=None, max_offset=0, warn_before_max_offset=0 ):
        """ creates a new symbolic link to the given snapshot into the destination directory
        
                no action is taken if the timeline has been frozen!

                if <max_offset> is set, links are affected when new snapshots are created, i.e. the max_offset parameter defines the
                    max. amount of snapshots that the link is allowed to stay "pinned" to a given snapshot. When this limit is reached,
                    the link is updated to point to it's nearest "more recent" neighbour snapshot

                if <max_offset> is set to 0 (default), then max_offset=<max_snapshots>
        """

        if snapshot is None:
            snapshot = self._get_latest_snapshot()

        self.logger.info( 'creating new link [{0}] to snapshot [{1}]'.format( link, snapshot ))

        if not isalnum( link, '-_.' ):
            raise Exception( 'link name must only consist of alpha-numeric characters, dots, underscores and dashes' )

        self._check_frozen()
        self._valid_snapshot( snapshot )

        if link in self._links:
            raise Exception( 'link [{0}] already exists!'.format( link ))

        if max_offset:
            if self._get_snapshot_offset( snapshot ) > max_offset:
                self.logger.warning( 'creating link to snapshot with offset [{0}] which already lies beyond max_offset [{1}]!'.format( self._get_snapshot_offset( snapshot ), max_offset ))

        link_path = os.path.join( self._destination, link )
        self._links[ link ] = { 'created' : datetime.now(), 'snapshot' : snapshot, 'path' : link_path, 'max_offset' : max_offset, 'warn_before_max_offset' : warn_before_max_offset }
        self._snapshots[ snapshot ][ 'links' ].append(link)
        self.save()

        # make changes in the file system
        subprocess.check_call(['ln', '-s', snapshot, link_path ])

        self.logger.debug( 'created new link [{0}] to snapshot [{1}]'.format( link, snapshot ))


    def delete_link( self, link ):
        """ deletes the given link
        
                no action is taken if the timeline has been frozen!
        """

        self.logger.info( 'deleting link [{0}]'.format( link ))

        self._check_frozen()
        self._valid_link( link, fail_on_disk_check=False )

        # remove link from snapshot
        snapshot = self._links[ link ][ 'snapshot' ]
        self._snapshots[ snapshot ][ 'links' ].remove( link )

        deleted_link = self._links.pop(link)
        self.save()

        # make changes in the file system
        subprocess.check_call(['rm', '-f', deleted_link['path'] ])

        self.logger.debug( 'deleted link [{0}] [{1}]'.format( link, deleted_link ))


    def update_link( self, link, snapshot=None ):
        """ updates link to point to the given snapshot
        
                no action is taken if the timeline has been frozen!
        """

        # TODO: warn_before_max_offset

        if snapshot is None:
            snapshot = self._get_latest_snapshot()

        self.logger.info( 'updating link [{0}] to snapshot [{1}]'.format( link, snapshot ))

        self._check_frozen()
        self._valid_link( link )
        self._valid_snapshot( snapshot )

        if snapshot == self._links[ link ][ 'snapshot' ]:
            self.logger.warning('link [{0}] already points to snapshot [{1}]!'.format( link, snapshot ))

        if self._links[ link ][ 'max_offset' ]:
            if self._get_snapshot_offset( snapshot ) > self._links[ link ][ 'max_offset' ]:
                self.logger.warning( 'updating link to snapshot with offset [{0}] which lies beyond specified max_offset [{1}]!'.format( self._get_snapshot_offset( snapshot ), self._links[ link ][ 'max_offset' ] ))

        # remove link from old snapshot
        old_snapshot = self._links[ link ][ 'snapshot' ]
        self._snapshots[ old_snapshot ][ 'links' ].remove( link )

        # add link to new snapshot
        self._snapshots[ snapshot ][ 'links' ].append(link)

        # finally update link to point to the new snapshot
        self._links[ link ][ 'snapshot' ] = snapshot

        self.save()

        # make changes in the file system
        subprocess.check_call(['ln', '-snf', snapshot, self._links[ link ][ 'path' ] ])

        self.logger.info( 'updated link [{0}] to snapshot [{1}]'.format( link, snapshot ))


    def rotate_snapshots( self ):
        """ rotate snapshots, i.e. delete old snapshots until max_snapshots are reached
        
                links are handled appropriately
        """

        # remove oldest snapshot(s)
        while len(self._lsnapshots) > self._max_snapshots:
            self.delete_snapshot( self._lsnapshots[0] )

        # update all links to be kept pinned within their <max_offset>
        for lk, link in self._links.items():
            if link[ 'max_offset' ]:
                if self._get_snapshot_offset(link[ 'snapshot' ]) > link[ 'max_offset' ]:
                    #self.update_link( lk, self._get_neighbour_snapshot( link[ 'snapshot' ] ))
                    self.update_link( lk, self._lsnapshots[-link[ 'max_offset' ]] )


    def consistency_check( self ):
        """ looks for missing snapshots and missing links and fixes metadata appropriately """

        self.logger.info( 'checking links...' )
        for link in self._links.keys():
            if not self._valid_link( link, fail_on_disk_check=False ):
                self.logger.warning( 'deleting invalid link [{0}]'.format( self._links[link]['path'] ))
                self.delete_link( link )

        self.logger.info( 'checking snapshots...' )
        for snapshot in self._lsnapshots:
            if not self._valid_snapshot( snapshot, fail_on_disk_check=False ):
                self.logger.warning( 'deleting invalid snapshot [{0}]'.format( self._snapshots[snapshot]['path'] ))
                self.delete_snapshot( snapshot )


    def _get_latest_snapshot( self ):
        """ helper method to return the latest snapshot """

        if len( self._lsnapshots ) == 0:
            raise Exception( 'no snapshots were found' )

        return self._lsnapshots[-1]


    def _get_neighbour_snapshot( self, snapshot ):
        """ helper method to find and return the nearest (preferably the more recent) neighbour snapshot
                
                if no neighbours are found, the last snapshot itself is returned
        """
        
        self._valid_snapshot( snapshot )

        snapshot_index = self._lsnapshots.index( snapshot )

        # if we only have a single snapshot left we return it as it's neighbour...
        if len(self._lsnapshots) == 1:
            neighbour_snapshot_index = snapshot_index

        # the neighbour of the latest snapshot must be an older snapshot...
        elif snapshot_index == (len(self._lsnapshots) - 1):
            neighbour_snapshot_index = snapshot_index - 1

        # in any other case we find the nearest more recent snapshot
        else:
            neighbour_snapshot_index = snapshot_index + 1

        return self._lsnapshots[ neighbour_snapshot_index ]


    def _get_snapshot_offset( self, snapshot ):
        """ helper method to return the offset of a given snapshot to the "upstream" snapshot """
        
        self._valid_snapshot( snapshot )

        return len(self._lsnapshots) - self._lsnapshots.index( snapshot )


    def _check_frozen( self ):
        """ helper method to abort if timeline is frozen """
        
        if self._frozen:
            raise Exception('timeline is frozen!')


    def _valid_snapshot( self, snapshot, fail_on_disk_check=True ):
        """ helper method to check for a valid snapshot """
        
        if not snapshot in self._snapshots:
            raise Exception('snapshot [{0}] not found!'.format( snapshot ))

        if not os.path.exists( self._snapshots[ snapshot ][ 'path' ] ):
            msg = 'snapshot [{0}] not found!'.format( self._snapshots[ snapshot ][ 'path' ] )
            if fail_on_disk_check:
                raise Exception( msg )
            self.logger.warning( msg )
            return False

        return True


    def _valid_link( self, link, fail_on_disk_check=True ):
        """ helper method to check for a valid link """
        
        if not link in self._links:
            raise Exception('link [{0}] not found!'.format( link ))

        if not os.path.islink( self._links[ link ][ 'path' ] ):
            msg = 'link [{0}] not found!'.format( self._links[ link ][ 'path' ] )
            if fail_on_disk_check:
                raise Exception( msg )
            self.logger.warning( msg )
            return False

        if not os.path.exists( self._links[ link ][ 'path' ] ):
            msg = 'link [{0}] is broken!'.format( self._links[ link ][ 'path' ] )
            if fail_on_disk_check:
                raise Exception( msg )
            self.logger.warning( msg )
            return False

        return True



if __name__ == '__main__':

    # TODO should write some proper tests...

    # create a logger
    logger = logging.getLogger('Timeline')
    logger.setLevel(logging.DEBUG)

    # console handler
    ch = logging.StreamHandler(sys.stdout)

    # set the logging level
    ch.setLevel( logging.DEBUG )

    # bind the console handler to the root logger
    #logging.getLogger().addHandler(ch)

    # bind the console handler to the logger
    logger.addHandler(ch)

    # write debug messages to /tmp/mrepo.log
    logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-13s: %(levelname)-8s %(message)s',
                    #datefmt='%y-%m-%d %H:%M',
                    #datefmt='%Y-%m-%d %H:%M',
                    #datefmt='%D %H:%M',
                    datefmt='%Y-%m-%d %T',
                    filename='/tmp/timeline.log',
                    filemode='w')

    epel = Timeline( 'epel', '/tmp/epel.tst', '/tmp/epel.dst', max_snapshots=15 )
    epel.save()
    epel = Timeline.load( '/tmp/epel.dst' )
    epel._debug = True
    epel.create_snapshot()
    epel.create_link( 'epel.grid', max_offset=1 )
    ##epel.create_link( 'epel.desktops', epel._lsnapshots[-1], max_offset=7 )
    ##epel.create_link( 'epel.dcache', epel._lsnapshots[-1] )
    epel.create_snapshot()
    epel.create_snapshot()
    for i in range(epel._max_snapshots):
        epel.create_snapshot()

    #epel.set_max_snapshots( 10 )

    #l = epel._lsnapshots[:]
    #for i in l:
    #    epel.delete_snapshot(i)

