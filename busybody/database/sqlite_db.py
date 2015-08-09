import logging
from playhouse.csv_loader import dump_csv
from playhouse.shortcuts import model_to_dict

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

    def fetch_retry_queue(self):
        """
        Return all rows from the failure_log table that still need to be retried
        """
        query = (FailureLog
            .select()
            .where(
                (
                    # specific codes that indicate we need to retry
                    #   - 202: explicit retry call
                    #   - 403: rate limit or auth rejection
                    #   - 500: server error, not our fault
                    (FailureLog.initial_status == 202) |
                    (FailureLog.initial_status == 403) |
                    (FailureLog.initial_status == 500)
                )
                # a retry can complete without succeeding (i.e. if  we go from 202 -> 404)
                & (FailureLog.retry_complete == 0)
            )
        )
        return [model_to_dict(result) for result in query]

    def dump_failures(self, outf_path, include_completed=False):
        """ Dump a CSV of failures to the specified location

        @param outf_path: Path of output file
        @param include_completed: Whether to include completed retries
        @return: None
        """
        if include_completed:
            q = FailureLog.select()
        else:
            q = FailureLog.select().where(FailureLog.retry_complete == 0)

        with open(outf_path, 'w') as outf:
            dump_csv(q, outf)

    def update_retry_row(self, current_row_obj, new_result):
        # update the failure row to flag if our result has succeeded
        fq = (FailureLog
            .update(
                most_recent_retry_status=new_result.status,
                retry_count=FailureLog.retry_count + 1,
                retry_complete=(new_result.status not in [202, 403, 500, 400, 422]),
                most_recent_retry_dt=datetime.datetime.now()
            )
            .where(
                FailureLog.request_id == current_row_obj['request_id']
            )
        )
        fq.execute()

        # get the updated row
        return FailureLog.select().where(FailureLog.request_id == current_row_obj['request_id'])
