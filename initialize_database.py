import os
import argparse

from busybody.models import *
from busybody.colors import Colors


if __name__ == '__main__':
    # parse command-line arguments
    parser = argparse.ArgumentParser(description='Initialize a busybody project database')
    parser.add_argument('-f', '--force', action='store_true', help='Remove an existing database ')
    args = parser.parse_args()

    # check whether we can safely configure the database
    print Colors.BOLD + '\nConfiguring BusyBody database...' + Colors.ENDC
    print Colors.OKBLUE + '  Checking for existing database...' + Colors.ENDC

    # execute database setup
    if os.path.exists('busybody.sqlite') and not args.force:
        print Colors.FAIL + '    FAILURE: ' + Colors.ENDC + 'The busybody database is already initialized. Run this script with -f to force database setup'
        print Colors.FAIL + 'FAILED\n' + Colors.ENDC
    else:
        if os.path.exists('busybody.sqlite'):
            print Colors.WARNING + '    WARNING: ' + Colors.ENDC + 'An existing busybody database will be overwritten'
            os.remove('busybody.sqlite')

        print '  Creating busybody database'
        db.connect()
        db.create_tables([
            User,
            UserAddress,
            UserDemography,
            UserProfile,
            UserTopic,
            UserOrganization,
            UserModelScore,
            FailureLog
        ])
        print Colors.OKGREEN + '    SUCCESS: ' + Colors.ENDC + 'Initialized busybody database'
        print Colors.OKGREEN + 'DONE\n' + Colors.ENDC
