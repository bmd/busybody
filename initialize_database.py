import os

from models import *


if __name__ == '__main__':
    # avoid conflicts with existing database
    if os.path.exists('busybody.sqlite'):
        print 'The busybody database is already initialized.\nDelete or move it to initialize a new copy.'
    else:
        print 'Creating busybody database'
        # create tables specified in 'models.py'
        db.connect()
        db.create_tables([
            User,
            UserAddress,
            UserDemography,
            UserProfile,
            UserTopic,
            UserOrganization,
            UserModelScore
        ])

        print 'Initialized Tables'
