import logging
import os
import argparse

from busybody import Colors
from busybody.database.models import *

# configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    filename='logs/testing.log',
    filemode='a'
)

console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
console.setFormatter(logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))

logger = logging.getLogger(__name__)
logger.addHandler(console)


if __name__ == '__main__':
    # parse command-line arguments
    parser = argparse.ArgumentParser(description='Initialize a busybody project database')
    parser.add_argument('-f', '--force', action='store_true', help='Remove an existing database ')
    args = parser.parse_args()

    # check whether we can safely configure the database
    logger.info('Configuring BusyBody database...')

    # execute database setup
    if os.path.exists('busybody.sqlite') and not args.force:
        logger.error(Colors.FAIL + 'FAILURE: The busybody database is already initialized. Run this script with -f to force database setup' + Colors.ENDC)
    else:
        if os.path.exists('busybody.sqlite'):
            logger.warn(Colors.WARNING + 'WARNING: An existing busybody database will be overwritten' + Colors.ENDC)
            os.remove('busybody.sqlite')

        db = SqliteDatabase('busybody.sqlite', threadlocals=True)
        db_proxy.initialize(db)
        logger.info('Creating busybody database')
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
        logger.info(Colors.OKGREEN + 'SUCCESS: Initialized busybody database' + Colors.ENDC)
