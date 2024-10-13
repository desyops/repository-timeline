#!/usr/bin/python3

"""Repository Timeline Tool"""

import argparse
import os
import subprocess
import sys
import lockfile
from timeline import timeline


def setup_argparse():
    """Setup argument parsing for CLI usage"""

    parser = argparse.ArgumentParser(
        description="",
    )

    subparsers = parser.add_subparsers(
        dest='subcommand',
        help='Available subcommands',
    )
    subparsers.required = True

    # config subcommand
    config_parser = subparsers.add_parser(
        'config',
        epilog=config.__doc__,
        formatter_class=argparse.RawTextHelpFormatter,
        help='Display timeline information or change advanced settings',
    )
    config_parser.set_defaults(func=config)
    config_parser.add_argument(
        'repository',
        action='store',
        metavar='REPOSITORY_LOCATION',
        help='Path to repository',
    )
    config_parser.add_argument(
        '--max-snapshots',
        help='change the max. amount of snapshots',
        type=int,
    )
    config_parser.add_argument(
        '--excludes',
        help='change the list of excludes',
        default=None,
    )
    config_parser.add_argument(
        '--freeze',
        action='store_true',
        help='freeze the timeline',
    )
    config_parser.add_argument(
        '--unfreeze',
        action='store_true',
        help='unfreeze the timeline',
    )
    config_parser.add_argument(
        '--consistency-check',
        action='store_true',
        help='check repository for consistency',
    )
    config_parser.add_argument(
        '-v', '--verbose', '--debug',
        action='store_true',
        dest='verbose',
        help='run in debug mode',
    )

    # create-default-links subcommand
    create_def_links_parser = subparsers.add_parser(
        'create-default-links',
        epilog=create_default_links.__doc__,
        formatter_class=argparse.RawTextHelpFormatter,
        help='Create default links'
    )
    create_def_links_parser.set_defaults(func=create_default_links)
    create_def_links_parser.add_argument(
        'repository',
        action='store',
        metavar='REPOSITORY_LOCATION',
        help='Path to repository',
    )

    # create-link subcommand
    create_link_parser = subparsers.add_parser(
        'create-link',
        epilog=create_link.__doc__,
        formatter_class=argparse.RawTextHelpFormatter,
        help='Create a new link',
    )
    create_link_parser.set_defaults(func=create_link)
    create_link_parser.add_argument(
        'repository',
        action='store',
        metavar='REPOSITORY_LOCATION/LINK_NAME',
        help='Path to repository with appended link name',
    )
    create_link_parser.add_argument(
        '--max-offset',
        help='make the link stay pinned to the snapshot with the given offset',
        type=int,
        default=0,
    )
    create_link_parser.add_argument(
        '--snapshot',
        help='snapshot to which the link should point',
        default=None,
    )

    # create-named-snapshot subcommand
    create_named_snap_parser = subparsers.add_parser(
        'create-named-snapshot',
        epilog=create_named_snap.__doc__,
        formatter_class=argparse.RawTextHelpFormatter,
        help='Create independent snapshot which is not managed within the timeline metadata',
    )
    create_named_snap_parser.set_defaults(func=create_named_snap)
    create_named_snap_parser.add_argument(
        'repository',
        action='store',
        metavar='REPOSITORY_LOCATION/SNAPSHOT_NAME',
        help='Path to repository with appended new snapshot name',
    )
    create_named_snap_parser.add_argument(
        '--source-snapshot',
        help='source snapshot from where to create the new snapshot',
        default=None,
    )
    create_named_snap_parser.add_argument(
        '--lock',
        action='store_true',
        help='use lockfile to protect against creating concurrent snapshots',
    )

    # create-repository subcommand
    create_repo_parser = subparsers.add_parser(
        'create-repo',
        epilog=create_repo.__doc__,
        formatter_class=argparse.RawTextHelpFormatter,
        help='Create new repository timeline',
    )
    create_repo_parser.set_defaults(func=create_repo)
    create_repo_parser.add_argument(
        'name',
        action='store',
        metavar='NAME',
        help='Name of the new repository',
    )
    create_repo_parser.add_argument(
        'source',
        action='store',
        metavar='SOURCE',
        help='Path to the source repository',
    )
    create_repo_parser.add_argument(
        'destination',
        action='store',
        metavar='DESTINATION',
        help='Destination path for the new timeline repository',
    )
    create_repo_parser.add_argument(
        '-i', '--initialize',
        action='store_true',
        help='initialize repository',
    )

    # create-snapshot subcommand
    create_snap_parser = subparsers.add_parser(
        'create-snapshot',
        epilog=create_snap.__doc__,
        formatter_class=argparse.RawTextHelpFormatter,
        help='Create new snapshot in a repository',
    )
    create_snap_parser.set_defaults(func=create_snap)
    create_snap_parser.add_argument(
        'repository',
        action='store',
        metavar='REPOSITORY_LOCATION',
        help='Path to repository',
    )
    create_snap_parser.add_argument(
        '--random-sleep',
        help='sleep a random amount of seconds [default=%(default)s] before taking snapshot',
        type=int,
        default=None,
    )
    create_snap_parser.add_argument(
        '--sleep-after',
        help='sleep the given amount of seconds after taking the snapshot',
        type=int,
        default=None,
    )
    create_snap_parser.add_argument(
        '--lock',
        action='store_true',
        help='use lockfile to protect against creating concurrent snapshots',
    )
    create_snap_parser.add_argument(
        '-v', '--verbose', '--debug',
        action='store_true',
        dest='verbose',
        help='run in debug mode',
    )

    # delete-link subcommand
    delete_link_parser = subparsers.add_parser(
        'delete-link',
        epilog=delete_link.__doc__,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    delete_link_parser.set_defaults(func=delete_link)
    delete_link_parser.add_argument(
        'repository',
        action='store',
        metavar='REPOSITORY_LOCATION/LINK_NAME',
        help='Path to repository with appended to be deleted link name',
    )

    # delete-snapshot subcommand
    delete_snap_parser = subparsers.add_parser(
        'delete-snapshot',
        epilog=delete_snap.__doc__,
        formatter_class=argparse.RawTextHelpFormatter,
        help='Delete snapshot from a repository',
    )
    delete_snap_parser.set_defaults(func=delete_snap)
    delete_snap_parser.add_argument(
        'repository',
        action='store',
        metavar='REPOSITORY_LOCATION/SNAPSHOT_NAME',
        help='Path to repository incl. snapshot name',
    )

    # rename-link subcommand
    rename_link_parser = subparsers.add_parser(
        'rename-link',
        epilog=rename_link.__doc__,
        formatter_class=argparse.RawTextHelpFormatter,
        help='Rename link in a repository',
    )
    rename_link_parser.set_defaults(func=rename_link)
    rename_link_parser.add_argument(
        'repository',
        action='store',
        metavar='REPOSITORY_LOCATION/LINK_NAME',
        help='Path to repository incl. link name',
    )
    rename_link_parser.add_argument(
        'linkname',
        action='store',
        metavar='NEW_LINK_NAME',
        help='New link name',
    )

    # update-link subcommand
    update_link_parser = subparsers.add_parser(
        'update-link',
        epilog=update_link.__doc__,
        formatter_class=argparse.RawTextHelpFormatter,
        help='Update link with new snapshot target',
    )
    update_link_parser.set_defaults(func=update_link)
    update_link_parser.add_argument(
        'repository',
        action='store',
        metavar='REPOSITORY_LOCATION/LINK_NAME',
        help='Path to repository incl. link name',
    )
    update_link_parser.add_argument(
        '--snapshot',
        help='Target SNAPSHOT_NAME for LINK_NAME',
        default=None,
    )

    arguments = parser.parse_args()

    return arguments


def config(options):
    """examples:
    %(prog)s /srv/repo/linux/ubuntu.timeline --freeze
    %(prog)s /srv/repo/linux/ubuntu.timeline --unfreeze
    %(prog)s /srv/repo/linux/ubuntu.timeline --consistency-check
    %(prog)s /srv/repo/linux/ubuntu.timeline --max-snapshots=42
    """

    t = timeline.Timeline.load(options.repository)

    if options.max_snapshots:
        t.set_max_snapshots( options.max_snapshots )
        t.rotate_snapshots()

    # we need to use None here
    # since user might want to clean the excludes value by using --excludes='
    if options.excludes is not None:
        t.set_excludes( options.excludes )
    if options.freeze:
        t.freeze()
    if options.unfreeze:
        t.unfreeze()
    if options.consistency_check:
        t.consistency_check()
    if options.verbose:
        print(t)
    t.save()


def create_default_links(options):
    """examples:
    %(prog)s /srv/repo/linux/ubuntu.timeline
    """

    t = timeline.Timeline.load(options.repository)
    t.create_link('upstream', max_offset=1)
    t.create_link('downstream')
    for i in (3, 7, 14, 21, 30, 60, 90):
        if t.get_max_snapshots() >= i:
            t.create_link(f'offset{i:03}', max_offset=i)


def create_link(options):
    """examples:
    %(prog)s /srv/repo/linux/ubuntu.timeline/myrepo.link
    %(prog)s /srv/repo/linux/ubuntu.timeline/myrepo.offset7 --max-offset=7
    %(prog)s /srv/repo/linux/ubuntu.timeline/myrepo.offset7 --snapshot=2015.02.12-141326 --max-offset=7
    """

    split_path = os.path.split(
        os.path.normpath(options.repository)
    )

    if options.snapshot and '/' in options.snapshot:
        options.snapshot = os.path.split(
            os.path.normpath(options.snapshot)
        )[1]
    t = timeline.Timeline.load(split_path[0])
    t.create_link(
        link=split_path[1],
        snapshot=options.snapshot,
        max_offset=options.max_offset
    )


def create_named_snap(options):
    """examples:
    %(prog)s /srv/repo/linux/ubuntu.timeline/myrepo
    %(prog)s /srv/repo/linux/ubuntu.timeline/myrepo --source-snapshot=2015.02.12-141326
    """

    split_path = os.path.split(
        os.path.normpath(options.repository)
    )

    if options.source_snapshot and '/' in options.source_snapshot:
        options.source_snapshot = os.path.split(
            os.path.normpath(options.source_snapshot)
        )[1]

    if options.lock:
        lock_file = os.path.join(split_path[0], '.lock')
        lock = lockfile.FileLock(lock_file)

        try:
            lock.acquire(timeout=1)
        except:
            if options.verbose:
                print(f'lockfile [{lock_file}] already locked')
            sys.exit(0)

    try:
        t = timeline.Timeline.load(split_path[0])
        t.create_named_snapshot(
            snapshot=split_path[1],
            source_snapshot=options.source_snapshot
        )
    except:
        if options.lock:
            lock.release()
        raise

    if options.lock:
        lock.release()


def create_repo(options):
    """examples:
    %(prog)s -i ubuntu /srv/repo/linux/ubuntu /srv/repo/linux/ubuntu.timeline
    """

    t = timeline.Timeline(options.name, options.source, options.destination)

    if options.initialize:
        t.create_snapshot()
        t.create_link('upstream', max_offset=1)
        t.create_link('downstream')
        for i in (3, 7, 14, 21, 30, 60, 90):
            t.create_link(f'offset{i:03}', max_offset=i)
    t.save()


def create_snap(options):
    """examples:
    %(prog)s /srv/repo/linux/ubuntu.timeline
    """

    if options.lock:
        lock_file = os.path.join(options.repository, '.lock')
        lock = lockfile.FileLock(lock_file)
        try:
            lock.acquire(timeout=1)
        except:
            if options.verbose:
                print(f'lockfile [{lock_file}] already locked')
            sys.exit(0)

    try:
        t = timeline.Timeline.load( options.repository )
        t.create_snapshot(
            random_sleep_before_snapshot=options.random_sleep,
            sleep_after_snapshot=options.sleep_after
        )
    except:
        if options.lock:
            lock.release()
        raise

    if options.lock:
        lock.release()


def delete_link(options):
    """examples:
    %(prog)s /srv/repo/linux/ubuntu.timeline/myrepo.link
    """

    split_path = os.path.split(os.path.normpath(options.repository))

    t = timeline.Timeline.load(split_path[0])
    t.delete_link(link=split_path[1])


def delete_snap(options):
    """examples:
    %(prog)s /srv/repo/linux/ubuntu.timeline/2015.02.12-141326
    """

    snapshot_path = os.path.normpath(options.repository)
    split_path = os.path.split(snapshot_path)

    t = timeline.Timeline.load(split_path[0])

    try:
        t.delete_snapshot(snapshot=split_path[1])
    except:
        # handle named snapshots
        if os.path.isdir( snapshot_path ):
            subprocess.check_call(['rm', '-rf', snapshot_path ])
            print(f'deleted unreferenced snapshot [{snapshot_path}]')
        else:
            print(f'WARNING: TRYING TO DELETE NON-EXISTING SNAPSHOT [{snapshot_path}]')
            raise


def rename_link(options):
    """examples:
    %(prog)s /srv/repo/linux/ubuntu.timeline/myrepo.link mynewrepo.link
    """

    split_path = os.path.split(os.path.normpath(options.repository))

    link_name = options.linkname
    if '/' in options.linkname:
        link_name = os.path.split(
            os.path.normpath(options.linkname)
        )[1]

    t = timeline.Timeline.load(split_path[0])
    l = t.delete_link(link=split_path[1])
    t.create_link(
        link=link_name,
        snapshot=l['snapshot'],
        max_offset=l['max_offset'],
        warn_before_max_offset=l['warn_before_max_offset']
    )


def update_link(options):
    """examples:
    %(prog)s /srv/repo/linux/ubuntu.timeline/myrepo.link
    %(prog)s /srv/repo/linux/ubuntu.timeline/myrepo.link --snapshot=2015.02.12-141326
    """

    split_path = os.path.split(
        os.path.normpath(options.repository)
    )

    if options.snapshot and '/' in options.snapshot:
        options.snapshot = os.path.split(
            os.path.normpath(options.snapshot)
        )[1]

    t = timeline.Timeline.load(split_path[0])
    t.update_link(
        link=split_path[1],
        snapshot=options.snapshot
    )


def main():
    """Main party"""
    args = setup_argparse()
    args.func(args)

if __name__ == '__main__':
    main()
