import datetime

from peewee import *

# initialize as a proxy object so that we can define the database at runtime
db_proxy = Proxy()

class BaseModel(Model):
    class Meta:
        database = db_proxy


class User(BaseModel):
    """ Model for the 'user' table """

    class Meta:
        db_table = 'user'

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
        null=True, decimal_places=2, default=0.0
    )
    create_dt = DateTimeField(
        default=datetime.datetime.now, index=True
    )
    update_dt = DateTimeField(
        default=None, null=True
    )


class UserAddress(BaseModel):
    """ Model for the 'user_address' table """

    class Meta:
        db_table = 'user_address'

    user_address_id = PrimaryKeyField()
    user = ForeignKeyField(
        User, related_name='addresses'
    )
    location_general = CharField(
        null=True, max_length=255
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
        null=True, decimal_places=2, default=0.0
    )
    create_dt = DateTimeField(
        default=datetime.datetime.now, index=True
    )
    update_dt = DateTimeField(
        null=True, default=None
    )


class UserDemography(BaseModel):
    """ Model for the 'user_demography' table """

    class Meta:
        db_table = 'user_demography'

    user_demography_id = PrimaryKeyField()
    user = ForeignKeyField(
        User, related_name='demographics'
    )
    gender = CharField(
        null=True, max_length=12, index=True
    )
    age = IntegerField(
        null=True, index=True
    )
    age_range_min = IntegerField(
        null=True, index=True
    )
    age_range_max = IntegerField(
        null=True, index=True
    )
    create_dt = DateTimeField(
        default=datetime.datetime.now, index=True
    )
    update_dt = DateTimeField(
        null=True, default=None
    )


class UserProfile(BaseModel):
    """ Model for the 'user_profile' table """

    class Meta:
        db_table = 'user_profile'

    user_profile_id = PrimaryKeyField()
    user = ForeignKeyField(
        User, related_name='profiles'
    )
    profile_type = CharField(  # chat, websites, and social profiles should all be handled by this model
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
    profile_id = CharField(
        null=True, default=None, max_length=255
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
        null=True, default=None
    )


class UserTopic(BaseModel):
    """ Model for the 'user_topic' table """

    class Meta:
        db_table = 'user_topic'

    user_topic_id = PrimaryKeyField()
    user = ForeignKeyField(
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
        null=True, default=None
    )


class UserOrganization(BaseModel):
    """ Model for the 'user_organization' table """

    class Meta:
        db_table = 'user_organization'

    user_organization_id = PrimaryKeyField()
    user = ForeignKeyField(
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
        null=True, default=None, index=True
    )
    is_primary = BooleanField(
        null=True, default=None, index=True
    )
    create_dt = DateTimeField(
        default=datetime.datetime.now
    )
    update_dt = DateTimeField(
        null=True, default=None
    )


class UserModelScore(BaseModel):
    """ Model for the user_model_score table """

    class Meta:
        db_table = 'user_model_score'

    user_model_score_id = PrimaryKeyField()
    user = ForeignKeyField(
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
    update_dt = DateTimeField(
        null=True, default=None
    )


class FailureLog(BaseModel):
    """ Model for the 'failure_log' table """

    class Meta:
        db_table = 'failure_log'

    failure_log_id = PrimaryKeyField()
    email = CharField(
        null=False, index=True, max_length=255
    )
    initial_status = IntegerField(
        index=True
    )
    message = TextField()
    request_id = CharField(
        max_length=255
    )
    create_dt = DateTimeField(
        default=datetime.datetime.now, index=True
    )
    most_recent_retry_dt = DateTimeField(
        null=True, default=None
    )
    most_recent_retry_status = IntegerField(
        null=True, default=None, index=True
    )
    retry_count = IntegerField(
        default=0
    )
    retry_complete = BooleanField(
        default=False, index=True
    )
