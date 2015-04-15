from peewee import *
from models import *
import datetime
import sys, os


if __name__ == '__main__':
	
	if os.path.exists('busybody.sqlite'):
		print 'The busybody database is already initialized.\nDelete or move it to initialize a new copy.'
	else:
		print 'Creating busybody database'

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
