from peewee import *
import datetime
import sys, os

if os.path.exists('busybody.sqlite'):
	sys.exit('>> The busybody database is already initialized.\n>> Delete or move it to initialize a new copy.')


db = SqliteDatabase('busybody.sqlite', threadlocals=True)

class BaseModel(Model):
	class Meta:
		database = db


class User(BaseModel):
	user_id = PrimaryKeyField()
	email = CharField(
		unique=True
	)
	first_name = CharField(
		index=True, null=True, max_length=32
	)
	last_name = CharField(
		index=True, null=True, max_length=32
	)
	match_likelihood = DecimalField(
		decimal_places=2, default=0.0
	)
	create_dt = DateTimeField(
		default=datetime.datetime.now, index=True
	)
	update_dt = DateTimeField(
		default=None, null=True
	)


class UserAddress(BaseModel):
	user_address_id = PrimaryKeyField()
	user_id = ForeignKeyField(
		User, related_name='addresses'
	)
	city_name = CharField(
		null=True, max_length=64
	)
	city_is_deduced = BooleanField(
		null=True
	)
	county_name = CharField(
		null=True, max_length=64
	)
	county_is_deduced = BooleanField(
		null=True
	)
	state_name = CharField(
		null=True, max_length=32
	)
	state_code = CharField(
		null=True, index=True, max_length=8
	)
	state_is_deduced = BooleanField(
		null=True, index=True
	)
	country_name = CharField(
		null=True, max_length=32
	)
	country_code = CharField(
		null=True, index=True, max_length=8
	)
	country_is_deduced = BooleanField(
		null=True, index=True
	)
	continent_name = CharField(
		null=True, max_length=32
	)
	continent_is_deduced = BooleanField(
		null=True
	)
	address_likelihood = DecimalField(
		decimal_places=2, default=0.0
	)
	create_dt = DateTimeField(
		default=datetime.datetime.now, index=True
	)
	update_dt = DateTimeField(
		default=None
	)


class UserDemography(BaseModel):
	user_demography_id = PrimaryKeyField()
	user_id = ForeignKeyField(
		User, related_name='demographics'
	)
	gender = CharField(
		null=True, max_length=12, index=True
	)
	age = IntegerField(
		index=True
	)
	age_range_min = IntegerField(
		index=True
	)
	age_range_max = IntegerField(
		index=True
	)
	create_dt = DateTimeField(
		default=datetime.datetime.now, index=True
	)
	update_dt = DateTimeField(
		default=None
	)


class UserProfile(BaseModel):
	user_profile_id = PrimaryKeyField()
	user_id = ForeignKeyField(
		User, related_name='profiles'
	)
	profile_type = CharField( # chat, websites, and social profiles should all be handled by this model
		max_length=32, index=True
	)
	network_id = CharField(
		max_length=32, index=True
	)
	network_name = CharField(
		max_length=32, index=True
	)
	profile_url = CharField(
		null=True, default=None
	)
	profile_id = IntegerField(
		null=True, default=None
	)
	user_name = CharField(
		null=True, default=None, max_length=64
	)
	user_bio = TextField(
		null=True, default=None
	)
	followers = IntegerField(
		null=True, default=None
	)
	following = IntegerField(
		null=True, default=None
	)
	user_feed = CharField(
		null=True, default=None
	)
	create_dt = DateTimeField(
		default=datetime.datetime.now, index=True
	)
	update_dt = DateTimeField(
		default=None
	)


class UserTopic(BaseModel):
	user_topic_id = PrimaryKeyField()
	user_id = ForeignKeyField(
		User, related_name='topics'
	)
	provider = CharField(
		null=False, index=True, max_length=32
	)
	topic = CharField(
		null=False, index=True, max_length=128
	)
	create_dt = DateTimeField(
		default=datetime.datetime.now, index=True
	)
	update_dt = DateTimeField(
		default=None
	)


class UserOrganization(BaseModel):
	user_organization_id = PrimaryKeyField()
	user_id = ForeignKeyField(
		User, related_name='organizations'
	)
	organization_name = CharField(
		null=True, default=None, max_length=128
	)
	title = CharField(
		null=True, default=None, max_length=64
	)
	start_date = CharField(  # yyyy-mm(-dd)
		null=True, default=None, max_length=10 
	)
	end_date = CharField(
		null=True, default=None, max_length=10
	)
	is_current = BooleanField(
		null=True, default=None
	)
	is_primary = BooleanField(
		null=True, default=None
	)
	create_dt = DateTimeField(
		default=datetime.datetime.now
	)
	update_dt = DateTimeField(
		default=None
	)


class UserModelScore(BaseModel):
	user_model_score_id = PrimaryKeyField()
	user_id = ForeignKeyField(
		User, related_name='scores'
	)
	provider = CharField(
		index=True, max_length=32
	)
	type = CharField(
		index=True, max_length=32
	)
	score_value = DecimalField(
		decimal_places=2, default=0.0
	)
	create_dt = DateTimeField(
		default=datetime.datetime.now
	)
	update_dt = DateTimeField(default=None)


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

print 'Created Tables'
