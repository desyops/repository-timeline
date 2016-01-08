# DESY Repository Management Tool

## Description
The DESY Repository Management Tool allows creating nightly snapshots from RedHat/CentOS and/or Ubuntu/Debian repositories.

The goal is to allow a way of controlling how our repository mirrors are "released" to the different classes of machines managed @ DESY.

The following scenario should give you an idea:

Hosts managed at DESY are split into 3 different classes (Class A, Class B and Class C).

- Class A hosts should get the latest updates directly from the upstream repositories.
- Class B hosts should be a bit "safer", i.e. their repositories are kept a whole week behind the repositories of Class A hosts. In case of a repository being broken, Class A hosts will get broken before Class B hosts. This way you have time to react.
- Class C hosts are even "safer" than Class B, i.e. they stay 2 weeks behind the upstream repositories.

This translates into the following use-case:

- IT Desktops from the Linux-Systems group: configured to the upstream repositories, i.e. always get the latest package updates! (Class A)
- Remaining IT Desktops: 7 days behind the upstream repositories (Class B)
- IT Non-Critical Servers: 7 days behind the upstream repositories (Class B)
- IT Critical Servers: 2 weeks behind the upstream repositories (Class C)
- External Desktops: 2 weeks behind the upstream repositories (Class C)
- External Servers: 2 weeks behind the upstream repositories (Class C)

This tool does not take care of synchronizing the repositories from their original location into a local storage (mirroring). It only takes care of managing the local mirror directories in your repository server.


## How does this work
The management of the repositories is done by creating a "timeline" for each repository. Each timeline contains a defined amount of snapshots from the directory tree of the given repository.
The snapshots within the timeline are taken on a nightly basis by simply calling 'cp -al' from the source directory of the repository into the timeline directory. This creates a complete copy of the source directory by hard-linking files into the destination directory. For more infos type 'man cp'.
When the maximum amount of snapshots is reached, the oldest snapshot gets deleted. The Class A, Class B and Class C references are simply a bunch of symbolic links which point to the appropriate snapshots.

The whole timeline machinery was written in python and can also be used for other purposes than repository management. The code sections for repository management are isolated and could easily be replaced or discarded without affecting the internal working of the timeline class.


## Installation
In order to use the repository management tool you just need to clone the git repository and configure the logging options by editing timeline-logging.cfg. This file is a standard python logging configuration file. For more details check out the [Logging facility for Python](https://docs.python.org/2/library/logging.html).


## Usage
Every script can be called without arguments (or with option -h) to show a little help dialog.
```
$ ./mrepo-create-repository.py -h

Usage:

mrepo-create-repository.py [options] NAME SOURCE DESTINATION

    example: mrepo-create-repository.py -i ubuntu /srv/repo/linux/ubuntu /srv/repo/linux/ubuntu.timeline


Options:
  --version         show program's version number and exit
  -h, --help        show this help message and exit
  -i, --initialize  initialize repository
```


### Creating a new repository timeline
Let's try to create a new timeline for a dummy repository...
```
./mrepo-create-repository.py -i dummyrepo /etc/skel /tmp/skel.timeline
```

In this case our dummy repository is the ```/etc/skel``` folder and our destination directory for creating our timeline is ```/tmp/skel.timeline```.

Most probably you will get the following error calling the previous command:
```
./mrepo-create-repository.py -i dummyrepo /etc/skel/ /tmp/skel.timeline
2016-01-06 16:49:30 - Timeline - INFO - configuring timeline [dummyrepo] from source [/etc/skel/] into destination [/tmp/skel.timeline]
2016-01-06 16:49:30 - Timeline.dummyrepo - INFO - creating new snapshot [2016.01.06-164930]
2016-01-06 16:49:30 - Timeline.dummyrepo - INFO - saving current timeline state...
cp: cannot create hard link ‘/tmp/skel.timeline/2016.01.06-164930/.mkshrc’ to ‘/etc/skel/.mkshrc’: Invalid cross-device link
Traceback (most recent call last):
  File "./mrepo-create-repository.py", line 26, in <module>
    t.create_snapshot()
  File "/afs/desy.de/user/e/engels/work/systems/desyops-git-repos/mrepo/timeline/timeline.py", line 450, in create_snapshot
    self._snapshot_copy_by_hardlink( self._source, snapshot_path )
  File "/afs/desy.de/user/e/engels/work/systems/desyops-git-repos/mrepo/timeline/timeline.py", line 329, in _snapshot_copy_by_hardlink
    subprocess.check_call(['cp', '-al', source_obj, snapshot_path ])
  File "/usr/lib/python2.7/subprocess.py", line 540, in check_call
    raise CalledProcessError(retcode, cmd)
subprocess.CalledProcessError: Command '['cp', '-al', '/etc/skel/.mkshrc', '/tmp/skel.timeline/2016.01.06-164930']' returned non-zero exit status 1
```

This means that we are trying to create a repository timeline in a device other than the one where the source directory of your repository is located (/tmp and /etc are mounted as different devices). In other words, you can only create snapshots from a repository within the same device. This is due to the natural constraints of using hard-links in the linux operating system (https://en.wikipedia.org/wiki/Hard_link#Limitations_of_hard_links).

Let's make our dummy example work by creating everything within /tmp.
```
rm -rf /tmp/skel.timeline
cp -a /etc/skel /tmp/
./mrepo-create-repository.py -i dummyrepo /tmp/skel /tmp/skel.timeline
2016-01-07 12:17:21 - Timeline - INFO - configuring timeline [dummyrepo] from source [/tmp/skel] into destination [/tmp/skel.timeline]
2016-01-07 12:17:21 - Timeline.dummyrepo - INFO - creating new snapshot [2016.01.07-121721]
2016-01-07 12:17:21 - Timeline.dummyrepo - INFO - saving current timeline state...
2016-01-07 12:17:21 - Timeline.dummyrepo - INFO - creating new link [upstream] to snapshot [2016.01.07-121721]
2016-01-07 12:17:21 - Timeline.dummyrepo - INFO - saving current timeline state...
2016-01-07 12:17:21 - Timeline.dummyrepo - INFO - creating new link [downstream] to snapshot [2016.01.07-121721]
2016-01-07 12:17:21 - Timeline.dummyrepo - INFO - saving current timeline state...
2016-01-07 12:17:21 - Timeline.dummyrepo - INFO - creating new link [offset003] to snapshot [2016.01.07-121721]
2016-01-07 12:17:21 - Timeline.dummyrepo - INFO - saving current timeline state...
...
```

That's basically it. We have now created a new repository timeline. Let's have a look:
```
ls -l /tmp/skel.timeline/
total 8
drwxr-xr-x 2 engels it 4096 Jan  7 12:17 2016.01.07-121721
lrwxrwxrwx 1 engels it   17 Jan  7 12:17 downstream -> 2016.01.07-121721
lrwxrwxrwx 1 engels it   17 Jan  7 12:17 offset003 -> 2016.01.07-121721
lrwxrwxrwx 1 engels it   17 Jan  7 12:17 offset007 -> 2016.01.07-121721
lrwxrwxrwx 1 engels it   17 Jan  7 12:17 offset014 -> 2016.01.07-121721
lrwxrwxrwx 1 engels it   17 Jan  7 12:17 offset021 -> 2016.01.07-121721
lrwxrwxrwx 1 engels it   17 Jan  7 12:17 offset030 -> 2016.01.07-121721
lrwxrwxrwx 1 engels it   17 Jan  7 12:17 offset060 -> 2016.01.07-121721
lrwxrwxrwx 1 engels it   17 Jan  7 12:17 offset090 -> 2016.01.07-121721
-rw-r--r-- 1 engels it 1658 Jan  7 12:17 timeline.cfg
lrwxrwxrwx 1 engels it   17 Jan  7 12:17 upstream -> 2016.01.07-121721
```

Since the script was called using the option '-i', it created already an initial snapshot (2016.01.07-121721) and a few symbolic links.

We can of course check if the copy was really done by hard-linking:
```
stat /tmp/skel/examples.desktop
  File: ‘/tmp/skel/examples.desktop’
  Size: 8980        Blocks: 24         IO Block: 4096   regular file
Device: 803h/2051d  Inode: 109         Links: 2
...

stat /tmp/skel.timeline/2016.01.07-121721/examples.desktop 
  File: ‘/tmp/skel.timeline/2016.01.07-121721/examples.desktop’
  Size: 8980        Blocks: 24         IO Block: 4096   regular file
Device: 803h/2051d  Inode: 109         Links: 2
...
```


### Creating new snapshots
Example how to create a new snapshot for the newly created repository:
```
./mrepo-create-snapshot.py /tmp/skel.timeline
2016-01-07 13:54:56 - Timeline - INFO - loading timeline instance from [/tmp/skel.timeline/.timeline]
2016-01-07 13:54:56 - Timeline - INFO - configuring timeline [dummyrepo] from source [/tmp/skel] into destination [/tmp/skel.timeline]
2016-01-07 13:54:56 - Timeline.dummyrepo - INFO - loading timeline state...
2016-01-07 13:54:56 - Timeline.dummyrepo - INFO - timeline state loaded from [/tmp/skel.timeline/.timeline]
2016-01-07 13:54:56 - Timeline.dummyrepo - INFO - creating new snapshot [2016.01.07-135456]
2016-01-07 13:54:56 - Timeline.dummyrepo - INFO - saving current timeline state...
2016-01-07 13:54:56 - Timeline.dummyrepo - INFO - updating link [upstream] to snapshot [2016.01.07-135456]
2016-01-07 13:54:56 - Timeline.dummyrepo - INFO - saving current timeline state...
2016-01-07 13:54:56 - Timeline.dummyrepo - INFO - updated link [upstream] to snapshot [2016.01.07-135456]
```

Now we should see the new snapshot:
```
ls -l /tmp/skel.timeline/
total 12
drwxr-xr-x 2 engels it 4096 Jan  7 12:17 2016.01.07-121721
drwxr-xr-x 2 engels it 4096 Jan  7 13:54 2016.01.07-135456
lrwxrwxrwx 1 engels it   17 Jan  7 12:17 downstream -> 2016.01.07-121721
lrwxrwxrwx 1 engels it   17 Jan  7 12:17 offset003 -> 2016.01.07-121721
lrwxrwxrwx 1 engels it   17 Jan  7 12:17 offset007 -> 2016.01.07-121721
lrwxrwxrwx 1 engels it   17 Jan  7 12:17 offset014 -> 2016.01.07-121721
lrwxrwxrwx 1 engels it   17 Jan  7 12:17 offset021 -> 2016.01.07-121721
lrwxrwxrwx 1 engels it   17 Jan  7 12:17 offset030 -> 2016.01.07-121721
lrwxrwxrwx 1 engels it   17 Jan  7 12:17 offset060 -> 2016.01.07-121721
lrwxrwxrwx 1 engels it   17 Jan  7 12:17 offset090 -> 2016.01.07-121721
-rw-r--r-- 1 engels it 1658 Jan  7 13:54 timeline.cfg
lrwxrwxrwx 1 engels it   17 Jan  7 13:54 upstream -> 2016.01.07-135456
```

We also see that the 'upstream' link has been updated to the newly created snapshot (2016.01.07-135456).

If we create 2 new snapshots:
```
./mrepo-create-snapshot.py /tmp/skel.timeline
./mrepo-create-snapshot.py /tmp/skel.timeline
```

We can see that the offset003 link will stay pinned to the 3rd snapshot (2016.01.07-135456):
```
ls -l /tmp/skel.timeline/
total 20
drwxr-xr-x 2 engels it 4096 Jan  7 12:17 2016.01.07-121721
drwxr-xr-x 2 engels it 4096 Jan  7 13:54 2016.01.07-135456
drwxr-xr-x 2 engels it 4096 Jan  7 13:57 2016.01.07-135727
drwxr-xr-x 2 engels it 4096 Jan  7 13:57 2016.01.07-135729
lrwxrwxrwx 1 engels it   17 Jan  7 12:17 downstream -> 2016.01.07-121721
lrwxrwxrwx 1 engels it   17 Jan  7 13:57 offset003 -> 2016.01.07-135456
lrwxrwxrwx 1 engels it   17 Jan  7 12:17 offset007 -> 2016.01.07-121721
lrwxrwxrwx 1 engels it   17 Jan  7 12:17 offset014 -> 2016.01.07-121721
lrwxrwxrwx 1 engels it   17 Jan  7 12:17 offset021 -> 2016.01.07-121721
lrwxrwxrwx 1 engels it   17 Jan  7 12:17 offset030 -> 2016.01.07-121721
lrwxrwxrwx 1 engels it   17 Jan  7 12:17 offset060 -> 2016.01.07-121721
lrwxrwxrwx 1 engels it   17 Jan  7 12:17 offset090 -> 2016.01.07-121721
-rw-r--r-- 1 engels it 1658 Jan  7 13:57 timeline.cfg
lrwxrwxrwx 1 engels it   17 Jan  7 13:57 upstream -> 2016.01.07-135729
```


#### Creating named snapshots
Besides creating "regular" snapshots one can create a new "named" snapshot which will be a completely independent copy of the repository:
```
./mrepo-create-named-snapshot.py /tmp/skel.timeline/skel.mycopy
2016-01-07 14:01:25 - Timeline - INFO - loading timeline instance from [/tmp/skel.timeline/.timeline]
2016-01-07 14:01:25 - Timeline - INFO - configuring timeline [dummyrepo] from source [/tmp/skel] into destination [/tmp/skel.timeline]
2016-01-07 14:01:25 - Timeline.dummyrepo - INFO - loading timeline state...
2016-01-07 14:01:25 - Timeline.dummyrepo - INFO - timeline state loaded from [/tmp/skel.timeline/.timeline]
2016-01-07 14:01:25 - Timeline.dummyrepo - INFO - creating new snapshot [skel.mycopy]

ls -l /tmp/skel.timeline/
total 24
drwxr-xr-x 2 engels it 4096 Jan  7 12:17 2016.01.07-121721
drwxr-xr-x 2 engels it 4096 Jan  7 13:54 2016.01.07-135456
drwxr-xr-x 2 engels it 4096 Jan  7 13:57 2016.01.07-135727
drwxr-xr-x 2 engels it 4096 Jan  7 13:57 2016.01.07-135729
lrwxrwxrwx 1 engels it   17 Jan  7 12:17 downstream -> 2016.01.07-121721
lrwxrwxrwx 1 engels it   17 Jan  7 13:57 offset003 -> 2016.01.07-135456
lrwxrwxrwx 1 engels it   17 Jan  7 12:17 offset007 -> 2016.01.07-121721
lrwxrwxrwx 1 engels it   17 Jan  7 12:17 offset014 -> 2016.01.07-121721
lrwxrwxrwx 1 engels it   17 Jan  7 12:17 offset021 -> 2016.01.07-121721
lrwxrwxrwx 1 engels it   17 Jan  7 12:17 offset030 -> 2016.01.07-121721
lrwxrwxrwx 1 engels it   17 Jan  7 12:17 offset060 -> 2016.01.07-121721
lrwxrwxrwx 1 engels it   17 Jan  7 12:17 offset090 -> 2016.01.07-121721
drwxr-xr-x 2 engels it 4096 Jan  7 14:01 skel.mycopy
-rw-r--r-- 1 engels it 1658 Jan  7 13:57 timeline.cfg
lrwxrwxrwx 1 engels it   17 Jan  7 13:57 upstream -> 2016.01.07-135729
```

Note that this copy is completely independent. This means that it is not tracked in any way within the timeline metadata and will therefore not be affected by any of the timeline methods including snapshot rotation.


### Deleting snapshots
Let's remove 2 snapshots:
```
./mrepo-delete-snapshot.py /tmp/skel.timeline/2016.01.07-135727
./mrepo-delete-snapshot.py /tmp/skel.timeline/2016.01.07-121721

ls -l /tmp/skel.timeline
total 16
drwxr-xr-x 2 engels it 4096 Jan  7 13:54 2016.01.07-135456
drwxr-xr-x 2 engels it 4096 Jan  7 13:57 2016.01.07-135729
lrwxrwxrwx 1 engels it   17 Jan  7 14:05 downstream -> 2016.01.07-135456
lrwxrwxrwx 1 engels it   17 Jan  7 13:57 offset003 -> 2016.01.07-135456
lrwxrwxrwx 1 engels it   17 Jan  7 14:05 offset007 -> 2016.01.07-135456
lrwxrwxrwx 1 engels it   17 Jan  7 14:05 offset014 -> 2016.01.07-135456
lrwxrwxrwx 1 engels it   17 Jan  7 14:05 offset021 -> 2016.01.07-135456
lrwxrwxrwx 1 engels it   17 Jan  7 14:05 offset030 -> 2016.01.07-135456
lrwxrwxrwx 1 engels it   17 Jan  7 14:05 offset060 -> 2016.01.07-135456
lrwxrwxrwx 1 engels it   17 Jan  7 14:05 offset090 -> 2016.01.07-135456
drwxr-xr-x 2 engels it 4096 Jan  7 14:01 skel.mycopy
-rw-r--r-- 1 engels it 1658 Jan  7 14:05 timeline.cfg
lrwxrwxrwx 1 engels it   17 Jan  7 13:57 upstream -> 2016.01.07-135729
```

That's it. More details can be found in the log files:
```
tail /tmp/timeline-debug.log
2016-01-07 14:05:27 - timeline - Timeline.dummyrepo - INFO - 576 - updating link [offset090] to snapshot [2016.01.07-135456]
2016-01-07 14:05:27 - timeline - Timeline.dummyrepo - INFO - 227 - saving current timeline state...
2016-01-07 14:05:27 - timeline - Timeline.dummyrepo - INFO - 227 - saving current timeline state...
2016-01-07 14:05:27 - timeline - Timeline.dummyrepo - DEBUG - 233 - current state saved into [/tmp/skel.timeline/.timeline]
2016-01-07 14:05:27 - timeline - Timeline.dummyrepo - INFO - 604 - updated link [offset090] to snapshot [2016.01.07-135456]
2016-01-07 14:05:27 - timeline - Timeline.dummyrepo - INFO - 604 - updated link [offset090] to snapshot [2016.01.07-135456]
2016-01-07 14:05:27 - timeline - Timeline.dummyrepo - INFO - 227 - saving current timeline state...
2016-01-07 14:05:27 - timeline - Timeline.dummyrepo - INFO - 227 - saving current timeline state...
2016-01-07 14:05:27 - timeline - Timeline.dummyrepo - DEBUG - 233 - current state saved into [/tmp/skel.timeline/.timeline]
2016-01-07 14:05:27 - timeline - Timeline.dummyrepo - DEBUG - 490 - deleted snapshot [2016.01.07-121721] [{'path': '/tmp/skel.timeline/2016.01.07-121721', 'links': [], 'created': datetime.datetime(2016, 1, 7, 12, 17, 21, 551751)}]
```

The log files show that some symbolic links had to be relinked to a nearest neighbour due to the fact that the original snapshot they were pointing to has been removed.


#### Deleting named snapshots
As previously stated, named snapshots are not tracked by the timeline and can therefore be removed using regular linux tools such as 'rm'. However it's safer to remove them with the mrepo-delete-snapshot.py tool, since you might otherwise by accident remove a regular snapshot which is referenced in the timeline metadata.

```
./mrepo-delete-snapshot.py /tmp/skel.timeline/skel.mycopy
```

### Creating links
Example on how to create a new link:
```
./mrepo-create-link.py /tmp/skel.timeline/myskel.link

ls -l /tmp/skel.timeline
total 15
drwxr-xr-x 2 engels it 4096 Jan  7 13:54 2016.01.07-135456
drwxr-xr-x 2 engels it 4096 Jan  7 13:57 2016.01.07-135729
lrwxrwxrwx 1 engels it   17 Jan  7 14:05 downstream -> 2016.01.07-135456
lrwxrwxrwx 1 engels it   17 Jan  7 14:17 myskel.link -> 2016.01.07-135729
lrwxrwxrwx 1 engels it   17 Jan  7 13:57 offset003 -> 2016.01.07-135456
lrwxrwxrwx 1 engels it   17 Jan  7 14:05 offset007 -> 2016.01.07-135456
lrwxrwxrwx 1 engels it   17 Jan  7 14:05 offset014 -> 2016.01.07-135456
lrwxrwxrwx 1 engels it   17 Jan  7 14:05 offset021 -> 2016.01.07-135456
lrwxrwxrwx 1 engels it   17 Jan  7 14:05 offset030 -> 2016.01.07-135456
lrwxrwxrwx 1 engels it   17 Jan  7 14:05 offset060 -> 2016.01.07-135456
lrwxrwxrwx 1 engels it   17 Jan  7 14:05 offset090 -> 2016.01.07-135456
-rw-r--r-- 1 engels it 1658 Jan  7 14:17 timeline.cfg
lrwxrwxrwx 1 engels it   17 Jan  7 13:57 upstream -> 2016.01.07-135729
```

Per default, new links point to the newest (upstream) snapshot and do not have a max-offset value set. Links without max-offset stay pinned to their snapshot until max snapshots are reached. When this limit is reached, links are updated to stay pinned to the "oldest" (downstream) snapshot until they are updated to point to a "newer" snapshot.


#### Creating links with a max-offset value
To ensure that links are kept at a maximum offset, we need to use the option --max-offset, e.g.
```
./mrepo-create-link.py --max-offset=2 /tmp/skel.timeline/mylink.offset2

ls -l /tmp/skel.timeline
total 12
drwxr-xr-x 2 engels it 4096 Jan  7 13:54 2016.01.07-135456
drwxr-xr-x 2 engels it 4096 Jan  7 13:57 2016.01.07-135729
lrwxrwxrwx 1 engels it   17 Jan  7 14:05 downstream -> 2016.01.07-135456
lrwxrwxrwx 1 engels it   17 Jan  8 08:47 mylink.offset2 -> 2016.01.07-135729
lrwxrwxrwx 1 engels it   17 Jan  7 14:17 myskel.link -> 2016.01.07-135729
lrwxrwxrwx 1 engels it   17 Jan  7 13:57 offset003 -> 2016.01.07-135456
lrwxrwxrwx 1 engels it   17 Jan  7 14:05 offset007 -> 2016.01.07-135456
lrwxrwxrwx 1 engels it   17 Jan  7 14:05 offset014 -> 2016.01.07-135456
lrwxrwxrwx 1 engels it   17 Jan  7 14:05 offset021 -> 2016.01.07-135456
lrwxrwxrwx 1 engels it   17 Jan  7 14:05 offset030 -> 2016.01.07-135456
lrwxrwxrwx 1 engels it   17 Jan  7 14:05 offset060 -> 2016.01.07-135456
lrwxrwxrwx 1 engels it   17 Jan  7 14:05 offset090 -> 2016.01.07-135456
-rw-r--r-- 1 engels it 1658 Jan  8 08:47 timeline.cfg
lrwxrwxrwx 1 engels it   17 Jan  7 13:57 upstream -> 2016.01.07-135729
```

Let's check:
```
./mrepo-create-snapshot.py /tmp/skel.timeline
./mrepo-create-snapshot.py /tmp/skel.timeline

ls -l /tmp/skel.timeline
total 20
drwxr-xr-x 2 engels it 4096 Jan  7 13:54 2016.01.07-135456
drwxr-xr-x 2 engels it 4096 Jan  7 13:57 2016.01.07-135729
drwxr-xr-x 2 engels it 4096 Jan  8 08:48 2016.01.08-084852
drwxr-xr-x 2 engels it 4096 Jan  8 08:48 2016.01.08-084855
lrwxrwxrwx 1 engels it   17 Jan  7 14:05 downstream -> 2016.01.07-135456
lrwxrwxrwx 1 engels it   17 Jan  8 08:48 mylink.offset2 -> 2016.01.08-084852
lrwxrwxrwx 1 engels it   17 Jan  7 14:17 myskel.link -> 2016.01.07-135729
lrwxrwxrwx 1 engels it   17 Jan  8 08:48 offset003 -> 2016.01.07-135729
lrwxrwxrwx 1 engels it   17 Jan  7 14:05 offset007 -> 2016.01.07-135456
lrwxrwxrwx 1 engels it   17 Jan  7 14:05 offset014 -> 2016.01.07-135456
lrwxrwxrwx 1 engels it   17 Jan  7 14:05 offset021 -> 2016.01.07-135456
lrwxrwxrwx 1 engels it   17 Jan  7 14:05 offset030 -> 2016.01.07-135456
lrwxrwxrwx 1 engels it   17 Jan  7 14:05 offset060 -> 2016.01.07-135456
lrwxrwxrwx 1 engels it   17 Jan  7 14:05 offset090 -> 2016.01.07-135456
-rw-r--r-- 1 engels it 1658 Jan  8 08:48 timeline.cfg
lrwxrwxrwx 1 engels it   17 Jan  8 08:48 upstream -> 2016.01.08-084855
```

Looks good :)

Note that specifying max-offset=2 doesn't mean that the link will be set initially to the 2nd snapshot. For this purpose you still need to use the --snapshot option. (This might change in the future...) 


### Deleting links
Deleting links is done using mrepo-delete-link.py. E.g.
```
./mrepo-delete-link.py /tmp/skel.timeline/myskel.link

ls -l /tmp/skel.timeline
total 20
drwxr-xr-x 2 engels it 4096 Jan  7 13:54 2016.01.07-135456
drwxr-xr-x 2 engels it 4096 Jan  7 13:57 2016.01.07-135729
drwxr-xr-x 2 engels it 4096 Jan  8 08:48 2016.01.08-084852
drwxr-xr-x 2 engels it 4096 Jan  8 08:48 2016.01.08-084855
lrwxrwxrwx 1 engels it   17 Jan  7 14:05 downstream -> 2016.01.07-135456
lrwxrwxrwx 1 engels it   17 Jan  8 08:48 mylink.offset2 -> 2016.01.08-084852
lrwxrwxrwx 1 engels it   17 Jan  8 08:48 offset003 -> 2016.01.07-135729
lrwxrwxrwx 1 engels it   17 Jan  7 14:05 offset007 -> 2016.01.07-135456
lrwxrwxrwx 1 engels it   17 Jan  7 14:05 offset014 -> 2016.01.07-135456
lrwxrwxrwx 1 engels it   17 Jan  7 14:05 offset021 -> 2016.01.07-135456
lrwxrwxrwx 1 engels it   17 Jan  7 14:05 offset030 -> 2016.01.07-135456
lrwxrwxrwx 1 engels it   17 Jan  7 14:05 offset060 -> 2016.01.07-135456
lrwxrwxrwx 1 engels it   17 Jan  7 14:05 offset090 -> 2016.01.07-135456
-rw-r--r-- 1 engels it 1658 Jan  8 08:52 timeline.cfg
lrwxrwxrwx 1 engels it   17 Jan  8 08:48 upstream -> 2016.01.08-084855
```


### Renaming links
Since links are tracked by the timeline instance, they must be renamed using the appropriate tool (mrepo-rename-link.py), e.g.:
```
./mrepo-rename-link.py /tmp/skel.timeline/mylink.offset2 /tmp/skel.timeline/mylink.offset002

ls -l /tmp/skel.timeline
total 20
drwxr-xr-x 2 engels it 4096 Jan  7 13:54 2016.01.07-135456
drwxr-xr-x 2 engels it 4096 Jan  7 13:57 2016.01.07-135729
drwxr-xr-x 2 engels it 4096 Jan  8 08:48 2016.01.08-084852
drwxr-xr-x 2 engels it 4096 Jan  8 08:48 2016.01.08-084855
lrwxrwxrwx 1 engels it   17 Jan  7 14:05 downstream -> 2016.01.07-135456
lrwxrwxrwx 1 engels it   17 Jan  8 08:54 mylink.offset002 -> 2016.01.08-084852
lrwxrwxrwx 1 engels it   17 Jan  8 08:48 offset003 -> 2016.01.07-135729
lrwxrwxrwx 1 engels it   17 Jan  7 14:05 offset007 -> 2016.01.07-135456
lrwxrwxrwx 1 engels it   17 Jan  7 14:05 offset014 -> 2016.01.07-135456
lrwxrwxrwx 1 engels it   17 Jan  7 14:05 offset021 -> 2016.01.07-135456
lrwxrwxrwx 1 engels it   17 Jan  7 14:05 offset030 -> 2016.01.07-135456
lrwxrwxrwx 1 engels it   17 Jan  7 14:05 offset060 -> 2016.01.07-135456
lrwxrwxrwx 1 engels it   17 Jan  7 14:05 offset090 -> 2016.01.07-135456
-rw-r--r-- 1 engels it 1658 Jan  8 08:54 timeline.cfg
lrwxrwxrwx 1 engels it   17 Jan  8 08:48 upstream -> 2016.01.08-084855
```


### Updating links
Updating links to point to a different snapshot must also be done using the appropriate tool (mrepo-update-link.py), e.g.:
```
./mrepo-update-link.py /tmp/skel.timeline/mylink.offset002

ls -l /tmp/skel.timeline
total 20
drwxr-xr-x 2 engels it 4096 Jan  7 13:54 2016.01.07-135456
drwxr-xr-x 2 engels it 4096 Jan  7 13:57 2016.01.07-135729
drwxr-xr-x 2 engels it 4096 Jan  8 08:48 2016.01.08-084852
drwxr-xr-x 2 engels it 4096 Jan  8 08:48 2016.01.08-084855
lrwxrwxrwx 1 engels it   17 Jan  7 14:05 downstream -> 2016.01.07-135456
lrwxrwxrwx 1 engels it   17 Jan  8 08:55 mylink.offset002 -> 2016.01.08-084855
lrwxrwxrwx 1 engels it   17 Jan  8 08:48 offset003 -> 2016.01.07-135729
lrwxrwxrwx 1 engels it   17 Jan  7 14:05 offset007 -> 2016.01.07-135456
lrwxrwxrwx 1 engels it   17 Jan  7 14:05 offset014 -> 2016.01.07-135456
lrwxrwxrwx 1 engels it   17 Jan  7 14:05 offset021 -> 2016.01.07-135456
lrwxrwxrwx 1 engels it   17 Jan  7 14:05 offset030 -> 2016.01.07-135456
lrwxrwxrwx 1 engels it   17 Jan  7 14:05 offset060 -> 2016.01.07-135456
lrwxrwxrwx 1 engels it   17 Jan  7 14:05 offset090 -> 2016.01.07-135456
-rw-r--r-- 1 engels it 1658 Jan  8 08:55 timeline.cfg
lrwxrwxrwx 1 engels it   17 Jan  8 08:48 upstream -> 2016.01.08-084855
```

Per default links are updated to the upstream snapshot unless the option --snapshot is used to specify a specific snapshot.

Updating links doesn't affect the max-offset value. This means that when the max-offset value is reached the link is kept pinned to the max-offset snapshot. Let's check:
```
./mrepo-create-snapshot.py /tmp/skel.timeline
./mrepo-create-snapshot.py /tmp/skel.timeline

ls -l /tmp/skel.timeline
total 28
drwxr-xr-x 2 engels it 4096 Jan  7 13:54 2016.01.07-135456
drwxr-xr-x 2 engels it 4096 Jan  7 13:57 2016.01.07-135729
drwxr-xr-x 2 engels it 4096 Jan  8 08:48 2016.01.08-084852
drwxr-xr-x 2 engels it 4096 Jan  8 08:48 2016.01.08-084855
drwxr-xr-x 2 engels it 4096 Jan  8 08:57 2016.01.08-085724
drwxr-xr-x 2 engels it 4096 Jan  8 08:57 2016.01.08-085727
lrwxrwxrwx 1 engels it   17 Jan  7 14:05 downstream -> 2016.01.07-135456
lrwxrwxrwx 1 engels it   17 Jan  8 08:57 mylink.offset002 -> 2016.01.08-085724
lrwxrwxrwx 1 engels it   17 Jan  8 08:57 offset003 -> 2016.01.08-084855
lrwxrwxrwx 1 engels it   17 Jan  7 14:05 offset007 -> 2016.01.07-135456
lrwxrwxrwx 1 engels it   17 Jan  7 14:05 offset014 -> 2016.01.07-135456
lrwxrwxrwx 1 engels it   17 Jan  7 14:05 offset021 -> 2016.01.07-135456
lrwxrwxrwx 1 engels it   17 Jan  7 14:05 offset030 -> 2016.01.07-135456
lrwxrwxrwx 1 engels it   17 Jan  7 14:05 offset060 -> 2016.01.07-135456
lrwxrwxrwx 1 engels it   17 Jan  7 14:05 offset090 -> 2016.01.07-135456
-rw-r--r-- 1 engels it 1658 Jan  8 08:57 timeline.cfg
lrwxrwxrwx 1 engels it   17 Jan  8 08:57 upstream -> 2016.01.08-085727
```

Looks good :) ```mylink.offset002``` keeps pointing at the second snapshot.


### Advanced settings
For changing advanced settings or displaying timeline informations one needs to use the mrepo-config.py tool.


#### Display timeline summary
```
./mrepo-config.py -v /tmp/skel.timeline
```


#### Freezing the repository
Freezing the repository prevents most operations including creating new snapshots. This should only be used in emergency situations where the upstream repository is broken and you do not want to propagate the error to your production repositories. Let's check:
```
./mrepo-config.py --freeze /tmp/skel.timeline
2016-01-08 09:06:41 - Timeline - INFO - loading timeline instance from [/tmp/skel.timeline/.timeline]
2016-01-08 09:06:41 - Timeline - INFO - configuring timeline [dummyrepo] from source [/tmp/skel] into destination [/tmp/skel.timeline]
2016-01-08 09:06:41 - Timeline.dummyrepo - INFO - loading timeline state...
2016-01-08 09:06:41 - Timeline.dummyrepo - INFO - timeline state loaded from [/tmp/skel.timeline/.timeline]
2016-01-08 09:06:41 - Timeline.dummyrepo - INFO - timeline has been frozen by user [root]
2016-01-08 09:06:41 - Timeline.dummyrepo - INFO - saving current timeline state...

./mrepo-create-snapshot.py /tmp/skel.timeline
2016-01-08 09:07:08 - Timeline - INFO - loading timeline instance from [/tmp/skel.timeline/.timeline]
2016-01-08 09:07:08 - Timeline - INFO - configuring timeline [dummyrepo] from source [/tmp/skel] into destination [/tmp/skel.timeline]
2016-01-08 09:07:08 - Timeline.dummyrepo - INFO - loading timeline state...
2016-01-08 09:07:08 - Timeline.dummyrepo - INFO - timeline state loaded from [/tmp/skel.timeline/.timeline]
2016-01-08 09:07:08 - Timeline.dummyrepo - INFO - creating new snapshot [2016.01.08-090708]
Traceback (most recent call last):
  File "./mrepo-create-snapshot.py", line 42, in <module>
    t.create_snapshot( random_sleep_before_snapshot=options['random_sleep'], sleep_after_snapshot=options['sleep_after'])
  File "/afs/desy.de/user/e/engels/work/systems/desyops-git-repos/mrepo/timeline/timeline.py", line 438, in create_snapshot
    self._check_frozen()
  File "/afs/desy.de/user/e/engels/work/systems/desyops-git-repos/mrepo/timeline/timeline.py", line 687, in _check_frozen
    raise Exception('timeline is frozen!')
Exception: timeline is frozen!
```

Let's unfreeze it:
```
./mrepo-config.py --unfreeze /tmp/skel.timeline
2016-01-08 09:08:28 - Timeline - INFO - loading timeline instance from [/tmp/skel.timeline/.timeline]
2016-01-08 09:08:28 - Timeline - INFO - configuring timeline [dummyrepo] from source [/tmp/skel] into destination [/tmp/skel.timeline]
2016-01-08 09:08:28 - Timeline.dummyrepo - INFO - loading timeline state...
2016-01-08 09:08:28 - Timeline.dummyrepo - INFO - timeline state loaded from [/tmp/skel.timeline/.timeline]
2016-01-08 09:08:28 - Timeline.dummyrepo - INFO - timeline previously frozen by user [root] has been unfrozen by [root]
2016-01-08 09:08:28 - Timeline.dummyrepo - INFO - saving current timeline state...
```


#### Changing the maximum amount of snapshots
The maximum amount of snapshots can easily be changed as follows:
```
./mrepo-config.py --max-snapshots=10 /tmp/skel.timeline
```

The maximum amount of snapshots can also be changed in the timeline configuration file (see below).


### Timeline configuration file
Each timeline instance contains a configuration file where more advanced settings can be changed. For example which directories should be excluded when creating new snapshots or which directories/files should be "hard-copied" instead of "hard-linked".


#### Example of a timeline configuration file for a Yum repository (in this case Scientific Linux)
```
cat /srv/repo/linux/scientific.timeline/timeline.cfg
[MAIN]
# ============================================================================================================================= =
# warning: this file is constantly auto-generated! do not be surprised if any comments get lost
# ============================================================================================================================= =
max_snapshots = 90
diff_log_path = /srv/repo/log/linux

[ADVANCED]
# ============================================================================================================================= =
# advanced options. do not touch this section unless you know what you are doing!
# options description:
#    excludes: colon-separated list of files/directories to be excluded when creating snapshots
#       no absolute paths allowed. only top-level paths or relative paths, e.g.
#       excludes = testing:dev:tmp:i386/builds
#       in this example the path i386/builds contains a subfolder. due to technical details these "relative paths" are not
#       skipped during the copy process. instead, they get deleted _after_ the copy process has taken place.
#    copy_files_recursive: colon-separated list of file names to be copied (i.e. not hard-linked) when creating snapshots
#    copy_dirs_recursive:  colon-separated list of directory names to be copied (i.e. not hard-linked) when creating snapshots
#       warning: the previous copy options perform a _recursive_ find in the source directory and _copy_ any found objects!
# ============================================================================================================================= =
excludes = sl41:sl42:303:304:305:307:308:309:30rolling:40:40rolling:41:42:43:44:45:46:47:48:49:50:51:510:511:52:53:54:55:56:57:58:59:5rolling:6.0:6.1:6.2:6.3:6.4
copy_files_recursive =
copy_dirs_recursive = repodata
```

We can see in this example that quite a number of objects are excluded during the snapshot process.

We can also see that all directories named "repodata" will be hard-copied when creating new snapshots. This setting is typical for other Yum repositories as well. The reason why this directory needs to be copied instead of hard-linking is because it contains the repository metadata.


#### Example of a timeline configuration file for a Debian repository (in this case Ubuntu)
```
cat /srv/repo/linux/ubuntu.timeline/timeline.cfg
[MAIN]
# ============================================================================================================================= =
# warning: this file is constantly auto-generated! do not be surprised if any comments get lost
# ============================================================================================================================= =
max_snapshots = 90
diff_log_path = /srv/repo/log/linux

[ADVANCED]
# ============================================================================================================================= =
# advanced options. do not touch this section unless you know what you are doing!
# options description:
#    excludes: colon-separated list of files/directories to be excluded when creating snapshots
#       no absolute paths allowed. only top-level paths or relative paths, e.g.
#       excludes = testing:dev:tmp:i386/builds
#       in this example the path i386/builds contains a subfolder. due to technical details these "relative paths" are not
#       skipped during the copy process. instead, they get deleted _after_ the copy process has taken place.
#    copy_files_recursive: colon-separated list of file names to be copied (i.e. not hard-linked) when creating snapshots
#    copy_dirs_recursive:  colon-separated list of directory names to be copied (i.e. not hard-linked) when creating snapshots
#       warning: the previous copy options perform a _recursive_ find in the source directory and _copy_ any found objects!
# ============================================================================================================================= =
excludes =
copy_files_recursive = Release:Release.gpg:InRelease:Contents-*.gz:Index
copy_dirs_recursive = binary-*:source
```

This example shows that we recursively copy all 'source' directories and all directories matching the regular expressions 'binary-*'. We also recursively copy all files matching the regular expression 'Contents-*.gz' and all files that are named 'Release', 'Release.gpg', 'InRelease' or 'Index'. This are typical settings for Debian-like repositories. 


