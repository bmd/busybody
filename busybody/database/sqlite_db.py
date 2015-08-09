import logging

from db_interface import AbstractDatabaseConnector
from models import *
from ..utils import SeekableDict, Colors

logger = logging.getLogger(__name__)


class SqliteConnector(AbstractDatabaseConnector):

    def __init__(self, connection_string):
        """ Set up a Sqlite database connection.

        @param connection_string: Name of Sqlite database to connect to
        @return: None
        """
        self.client = SqliteDatabase(connection_string, threadlocals=True)
        db_proxy.initialize(self.client)

        # explicitly check that the connection is ok
        logger.debug('Connecting to sqlite database {}'.format(connection_string))
        try:
            self.client.connect()
        except Exception, e:
            logger.error(Colors.FAIL + 'Failed to connect to database' + Colors.ENDC)
            logger.error(Colors.FAIL + str(e) + Colors.ENDC)
            raise

    def insert_user_record(self, email, record):
        """ Parse a user record returned by FullContact and insert it into the database

        @param email: Email that was searched
        @param record: Response returned by FullContact
        @return: None
        """
        record = SeekableDict(record)

        user_obj = User.create(
            email=email,
            first_name=record['contactInfo', 'givenName'],
            last_name=record['contactInfo', 'familyName'],
            match_likelihood=record['likelihood']
        )

        UserAddress.create(
            user=user_obj,
            location_general=record['demographics', 'locationGeneral'],
            city_name=record['demographics', 'locationDeduced', 'city', 'name'],
            city_is_deduced=record['demographics', 'locationDeduced', 'city', 'deduced'],
            county_name=record['demographics', 'locationDeduced', 'county', 'name'],
            county_is_deduced=record['demographics', 'locationDeduced', 'county', 'deduced'],
            state_name=record['demographics', 'locationDeduced', 'state', 'name'],
            state_code=record['demographics', 'locationDeduced', 'state', 'code'],
            state_is_deduced=record['demographics', 'locationDeduced', 'state', 'deduced'],
            country_name=record['demographics', 'locationDeduced', 'country', 'name'],
            country_code=record['demographics', 'locationDeduced', 'country', 'code'],
            country_is_deduced=record['demographics', 'locationDeduced', 'country', 'deduced'],
            continent_name=record['demographics', 'locationDeduced', 'continent', 'name'],
            continent_is_deduced=record['demographics', 'locationDeduced', 'continent', 'deduced'],
            address_likelihood=record['demographics', 'locationDeduced', 'likelihood']
        )

        base_age_range = record['demographics', 'ageRange']
        if base_age_range:
            age_min, age_max = base_age_range.split('-')[0], base_age_range.split('-')[1]
        else:
            age_min, age_max = None, None

        UserDemography.create(
            user=user_obj,
            gender=record['demographics', 'gender'],
            age=record['demographics', 'age'],
            age_range_min=age_min,
            age_range_max=age_max
        )

        organizations = record.__getitem__('organizations', default=list())
        for org in organizations:
            UserOrganization.create(
                user=user_obj,
                organization_name=org.get('name', ''),
                title=org.get('title', ''),
                start_date=org.get('startDate', None),
                end_date=org.get('endDate', None),
                is_current=org.get('current', 0),
                is_primary=org.get('isPrimary', 0)
            )

        topics = record.__getitem__(['digitalFootprint', 'topics', 'klout'], default=list())
        for topic in topics:
            UserTopic.create(
                user=user_obj,
                provider=topic.get('provider', ''),
                topic=topic.get('value', '')
            )

        scores = record.__getitem__(['digitalFootprint', 'scores', 'klout'], default=list())
        for score in scores:
            UserModelScore.create(
                user=user_obj,
                provider=score.get('provider', ''),
                type=score.get('general', ''),
                score_value=score.get('value', None)
            )

        websites = record.__getitem__(['contactInfo', 'websites'], default=list())
        for web in websites:
            UserProfile.create(
                user=user_obj,
                profile_type='website',
                network_id='website',
                network_name='website',
                profile_url=web.get('url', None)
            )

        profiles_raw = record.__getitem__(['socialProfiles'], default=list())
        profiles = []

        if type(profiles_raw) == dict:
            for network, profile in profiles_raw.items():
                profiles.extend([p for p in profile])
        elif type(profiles_raw) == list:
            profiles = [p for p in profiles_raw]

        for profile in profiles:
            UserProfile.create(
                user=user_obj,
                profile_type='social',
                network_id=profile.get('typeId', ''),
                network_name=profile.get('typeName'),
                profile_id=profile.get('id', ''),
                profile_url=profile.get('url', ''),
                user_name=profile.get('username', ''),
                user_bio=profile.get('bio', ''),
                followers=profile.get('followers', 0),
                following=profile.get('following', 0),
                user_feed=profile.get('rss', '')
            )

    def log_failure(self, email, failure_response):
        """ Log a failure response in the database

        @param email: Email that was submitted to the FullContact API
        @param failure_response: Response from the FullContact API
        @return: None
        """
        FailureLog.create(
            email=email,
            initial_status=failure_response.status,
            message=failure_response.message,
            request_id=failure_response.requestId,
            retry_complete=(failure_response.status not in [202, 403, 500, 400, 422])
        )
